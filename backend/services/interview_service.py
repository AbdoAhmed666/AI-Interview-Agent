"""Service layer for interview startup workflow."""

from datetime import datetime, timedelta
from typing import Any

try:
    from ..interview.interview_manager import InterviewManager
except ImportError:  # pragma: no cover - fallback for direct execution
    from interview.interview_manager import InterviewManager

from database import SessionLocal
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from repositories.interview_repository import (
    create_audit_event,
    create_session,
    create_question,
    get_current_question,
    get_session,
    get_question_for_session,
    get_question_for_session_for_update,
    get_question_by_number,
    get_session_for_update,
    list_questions,
    update_session_state,
    update_question,
)
from schemas import QuestionStatus, SessionStatus
from evaluator import evaluate_answer as evaluate_answer_with_llm
from adaptive_engine import AdaptiveEngine
from config import settings


class AnswerClaimError(Exception):
    """Base exception for authoritative answer-claim failures."""


class AnswerClaimNotFound(AnswerClaimError):
    """The session does not exist or is not owned by the caller."""


class AnswerClaimConflict(AnswerClaimError):
    """The session/question cannot accept another answer claim."""


class EvaluationPersistenceConflict(AnswerClaimError):
    """The claimed question changed before evaluation could be persisted."""


class GenerationConflict(AnswerClaimError):
    """The session cannot start or complete next-question generation."""


class FinishError(Exception):
    """Base exception for durable finish failures."""

    def __init__(self, message: str, status_code: int = 409) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class FinishNotFoundError(FinishError):
    def __init__(self, message: str = "Interview session not found") -> None:
        super().__init__(message, status_code=404)


class FinishForbidden(FinishError):
    def __init__(self, message: str = "You do not own this interview session") -> None:
        super().__init__(message, status_code=403)


class FinishConflict(FinishError):
    def __init__(self, message: str = "Cannot finish interview in current state") -> None:
        super().__init__(message, status_code=409)


class InterviewService:
    """Coordinate the interview workflow and persist sessions/questions to the DB.

    PostgreSQL is the authoritative source of truth for interview workflow
    state. The shared :class:`InterviewManager` is retained only as a holder of
    stateless AI/domain helpers (CV storage, parsing, analysis, eligibility,
    RAG, prompt building, and the LLM provider). It is never consulted as
    workflow state, and no process-local id mappings are kept.
    """

    _shared_manager: InterviewManager | None = None

    def __init__(self) -> None:
        if InterviewService._shared_manager is None:
            InterviewService._shared_manager = InterviewManager()
        # The manager is used only for its stateless AI/domain helper
        # components; its in-memory session bookkeeping is never read.
        self.manager = InterviewService._shared_manager

    @staticmethod
    def _start_durable_session(
        db: Session,
        user_id: int,
        role: str,
        first_question: str,
        difficulty: int,
    ) -> tuple[Any, Any]:
        """Persist the interview session and its first question atomically.

        Uses the repository layer (flush-only primitives); the caller owns the
        transaction via ``with db.begin()`` and the repository never commits.
        Both the session row and question #1 are prepared in the same
        transaction and committed together, so a failure while persisting the
        question rolls the session back as well.

        The first question is always created with ``question_number = 1`` and
        ``status = ACTIVE`` so it is immediately claimable by the durable
        ``claim_answer`` flow.
        """
        db_session = create_session(
            db=db,
            user_id=user_id,
            role=role,
        )
        db_question = create_question(
            db=db,
            session_id=db_session.id,
            question=first_question,
            difficulty=difficulty,
            question_number=1,
            status=QuestionStatus.ACTIVE,
        )
        create_audit_event(
            db=db,
            session_id=db_session.id,
            question_id=db_question.id,
            event_type="SESSION_STARTED",
            question_number=1,
            from_status=None,
            to_status=SessionStatus.IN_PROGRESS,
            created_at=datetime.utcnow(),
        )
        return db_session, db_question

    def start_interview(self, user_id: int, role: str) -> dict[str, Any]:
        """Start an interview: check eligibility, then persist a durable session + Q1.

        PostgreSQL is the sole workflow authority. The InterviewManager is used
        only for its stateless AI/domain helpers (CV storage, parsing, analysis,
        eligibility, and — via :meth:`_generate_question_text` — RAG/prompt/LLM).
        No process-local manager session state or id mappings are created; the
        returned ``session_id`` and ``question_id`` are always durable DB rows.

        The authoritative session and question #1 are created in PostgreSQL by
        :meth:`_start_durable_session` inside a single caller-owned transaction,
        so a failure while persisting Q1 rolls the session back as well.
        """
        # Eligibility uses only stateless domain helpers; it never touches
        # manager workflow state.
        if not self.manager.storage.has_cv(user_id):
            raise FileNotFoundError("Please upload your CV first.")

        cv_path = self.manager.storage.get_active_cv(user_id)
        document = self.manager.parser.parse(
            file_path=cv_path,
            role="user",
            document_type="cv",
        )
        analysis = self.manager.analyzer.analyze(document.content)

        eligibility_result = self.manager.eligibility.evaluate(analysis, role)
        if not eligibility_result.eligible:
            # Not compatible with the CV: return eligibility without creating a
            # DB session/question.
            return {
                "eligible": False,
                "message": eligibility_result.message,
                "score": eligibility_result.score,
                "recommended_roles": [
                    item.role for item in eligibility_result.recommended_roles
                ],
            }

        difficulty = 3
        first_question = self._validate_generated_question(
            self._generate_question_text(
                user_id=user_id,
                role=role,
                difficulty=difficulty,
            )
        )

        db = SessionLocal()
        try:
            with db.begin():
                db_session, db_question = self._start_durable_session(
                    db=db,
                    user_id=user_id,
                    role=role,
                    first_question=first_question,
                    difficulty=difficulty,
                )
                # Capture PKs before commit while they are guaranteed loaded.
                session_id = db_session.id
                question_id = db_question.id

            return {
                "eligible": True,
                "role": role,
                "difficulty": difficulty,
                "next_question": first_question,
                "first_question": first_question,
                "question": first_question,
                "session_id": session_id,
                "question_id": question_id,
            }
        finally:
            db.close()

    def claim_answer(
        self,
        user_id: int,
        session_id: int,
        question_id: int,
        answer: str,
    ) -> dict[str, Any]:
        """Durably claim an answer before any evaluation work occurs."""
        db = SessionLocal()
        try:
            with db.begin():
                result = self._claim_answer_in_transaction(
                    db=db,
                    user_id=user_id,
                    session_id=session_id,
                    question_id=question_id,
                    answer=answer,
                )
            return result
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _claim_answer_in_transaction(
        db,
        user_id: int,
        session_id: int,
        question_id: int,
        answer: str,
    ) -> dict[str, Any]:
        session = get_session_for_update(db, session_id, user_id=user_id)
        if session is None:
            raise AnswerClaimNotFound("Interview session not found")

        if session.status != SessionStatus.IN_PROGRESS.value:
            raise AnswerClaimConflict("Interview session cannot accept an answer")

        current_question = get_current_question(db, session_id, for_update=True)
        question = (
            current_question
            if current_question is not None and current_question.id == question_id
            else get_question_for_session_for_update(db, session_id, question_id)
        )
        if question is None:
            raise AnswerClaimConflict("Question is not the current active question")

        if question.question_number is None or not 1 <= question.question_number <= 5:
            raise AnswerClaimConflict("Question number is outside the interview range")

        if question.status != QuestionStatus.ACTIVE.value:
            if InterviewService._answers_equal(question.answer, answer):
                return {
                    "session_id": session.id,
                    "question_id": question.id,
                    "question_number": question.question_number,
                    "status": question.status,
                    "answer_submitted_at": question.answer_submitted_at,
                    "evaluation": question.evaluation,
                    "already_submitted": True,
                    "next_question": None,
                }
            raise AnswerClaimConflict("Question has already been submitted")

        if current_question is None or current_question.id != question_id:
            raise AnswerClaimConflict("Question is not the current active question")

        submitted_at = datetime.utcnow()
        update_session_state(
            db,
            session,
            status=SessionStatus.IN_PROGRESS,
            updated_at=submitted_at,
        )
        update_question(
            db,
            question,
            status=QuestionStatus.EVALUATING,
            answer=InterviewService._normalize_answer(answer),
            answer_submitted_at=submitted_at,
            evaluation=None,
            evaluated_at=None,
            score=None,
            feedback=None,
        )
        create_audit_event(
            db,
            session_id=session_id,
            question_id=question.id,
            event_type="ANSWER_SUBMITTED",
            question_number=question.question_number,
            from_status=QuestionStatus.ACTIVE,
            to_status=QuestionStatus.EVALUATING,
            created_at=submitted_at,
        )
        return {
            "session_id": session.id,
            "question_id": question.id,
            "question_number": question.question_number,
            "status": question.status,
            "answer_submitted_at": submitted_at,
            "evaluation": None,
            "next_question": None,
        }

    def evaluate_claimed_answer(
        self,
        user_id: int,
        session_id: int,
        question_id: int,
        just_claimed: bool = False,
    ) -> dict[str, Any]:
        """Evaluate a persisted answer, then atomically persist its result.

        ``just_claimed`` marks the caller as the worker whose own
        :meth:`claim_answer` moved this question ACTIVE -> EVALUATING moments
        ago, inside the same request. That caller already holds the evaluation
        lease, so it must not read its own fresh claim as somebody else's
        in-flight evaluation. Recovery callers (``/retry-evaluation``, the
        stale-lease takeover) leave it ``False`` and keep the full guard.
        """
        retry_started = False
        db = SessionLocal()
        try:
            session = get_session(db, session_id)
            # Enforce ownership before any fast-path return (e.g. the already
            # EVALUATED result below), so a non-owner can never read another
            # user's evaluation. A non-owner is treated as "not found".
            if session is None or session.user_id != user_id:
                raise AnswerClaimNotFound("Interview session not found")
            question = get_question_for_session(db, session_id, question_id)
            if question is None:
                raise EvaluationPersistenceConflict("Question not found for session")
            if session.status != SessionStatus.IN_PROGRESS.value:
                raise EvaluationPersistenceConflict("Interview session cannot be evaluated")
            if question.status == QuestionStatus.EVALUATED.value:
                return self._evaluation_result(question)
            if question.status == QuestionStatus.EVALUATION_FAILED.value:
                retry_started = self._claim_evaluation_retry(
                    user_id, session_id, question_id
                )
            elif question.status == QuestionStatus.EVALUATING.value:
                # Only a *foreign* claim blocks here: it is either still in
                # flight (conflict) or stale enough to take over (retry).
                if not just_claimed:
                    if not self._is_stale(question.answer_submitted_at):
                        raise EvaluationPersistenceConflict(
                            "Evaluation is still in progress"
                        )
                    retry_started = self._claim_evaluation_retry(
                        user_id, session_id, question_id
                    )
            else:
                raise EvaluationPersistenceConflict("Question is not awaiting evaluation")
            persisted_answer = question.answer
            role = session.role
            question_text = question.question
        finally:
            db.rollback()
            db.close()

        try:
            evaluation = evaluate_answer_with_llm(
                role=role,
                question=question_text,
                answer=persisted_answer or "",
            )
        except Exception as exc:
            self._persist_evaluation_failure(
                user_id=user_id,
                session_id=session_id,
                question_id=question_id,
                error_type=type(exc).__name__,
                retry_started=retry_started,
            )
            raise

        db = SessionLocal()
        try:
            with db.begin():
                session = get_session_for_update(db, session_id, user_id=user_id)
                if session is None:
                    raise AnswerClaimNotFound("Interview session not found")
                question = get_question_for_session_for_update(
                    db, session_id, question_id
                )
                if question is None:
                    raise EvaluationPersistenceConflict("Question not found for session")
                if question.status == QuestionStatus.EVALUATED.value:
                    return self._evaluation_result(question)
                if (
                    session.status != SessionStatus.IN_PROGRESS.value
                    or question.status != QuestionStatus.EVALUATING.value
                ):
                    raise EvaluationPersistenceConflict(
                        "Question changed before evaluation persistence"
                    )
                evaluated_at = datetime.utcnow()
                evaluation_data = evaluation.model_dump(mode="json")
                update_question(
                    db,
                    question,
                    status=QuestionStatus.EVALUATED,
                    evaluation=evaluation_data,
                    score=evaluation.score,
                    feedback=evaluation.feedback,
                    evaluated_at=evaluated_at,
                )
                create_audit_event(
                    db,
                    session_id=session_id,
                    question_id=question_id,
                    event_type="EVALUATION_SUCCEEDED",
                    question_number=question.question_number,
                    from_status=QuestionStatus.EVALUATING,
                    to_status=QuestionStatus.EVALUATED,
                    created_at=evaluated_at,
                )
                if retry_started:
                    create_audit_event(
                        db,
                        session_id=session_id,
                        question_id=question_id,
                        event_type="EVALUATION_RETRY_SUCCEEDED",
                        question_number=question.question_number,
                        from_status=QuestionStatus.EVALUATING,
                        to_status=QuestionStatus.EVALUATED,
                        created_at=evaluated_at,
                    )
                return self._evaluation_result(question)
        finally:
            db.close()

    def _persist_evaluation_failure(
        self,
        user_id: int,
        session_id: int,
        question_id: int,
        error_type: str,
        retry_started: bool = False,
    ) -> None:
        db = SessionLocal()
        try:
            with db.begin():
                session = get_session_for_update(db, session_id, user_id=user_id)
                if session is None:
                    raise AnswerClaimNotFound("Interview session not found")
                question = get_question_for_session_for_update(
                    db, session_id, question_id
                )
                if question is None:
                    raise EvaluationPersistenceConflict("Question not found for session")
                if question.status == QuestionStatus.EVALUATED.value:
                    return
                if question.status != QuestionStatus.EVALUATING.value:
                    raise EvaluationPersistenceConflict(
                        "Question changed before evaluation failure persistence"
                    )
                failed_at = datetime.utcnow()
                update_question(
                    db,
                    question,
                    status=QuestionStatus.EVALUATION_FAILED,
                )
                create_audit_event(
                    db,
                    session_id=session_id,
                    question_id=question_id,
                    event_type=(
                        "EVALUATION_RETRY_FAILED"
                        if retry_started
                        else "EVALUATION_FAILED"
                    ),
                    question_number=question.question_number,
                    from_status=QuestionStatus.EVALUATING,
                    to_status=QuestionStatus.EVALUATION_FAILED,
                    details={"error_type": error_type},
                    created_at=failed_at,
                )
                if retry_started:
                    create_audit_event(
                        db,
                        session_id=session_id,
                        question_id=question_id,
                        event_type="EVALUATION_FAILED",
                        question_number=question.question_number,
                        from_status=QuestionStatus.EVALUATING,
                        to_status=QuestionStatus.EVALUATION_FAILED,
                        details={"error_type": error_type},
                        created_at=failed_at,
                    )
        finally:
            db.close()

    @staticmethod
    def _is_stale(updated_at: datetime | None) -> bool:
        if updated_at is None:
            return True
        return datetime.utcnow() - updated_at >= timedelta(
            seconds=settings.interview_recovery_stale_seconds
        )

    @staticmethod
    def _normalize_answer(answer: str | None) -> str:
        """Canonical form of a candidate answer used for storage and comparison.

        Trims surrounding whitespace so the persisted answer and the duplicate
        check agree; internal content is left untouched.
        """
        return (answer or "").strip()

    @staticmethod
    def _answers_equal(first: str | None, second: str | None) -> bool:
        return (
            InterviewService._normalize_answer(first)
            == InterviewService._normalize_answer(second)
        )

    def _claim_evaluation_retry(
        self,
        user_id: int,
        session_id: int,
        question_id: int,
    ) -> bool:
        db = SessionLocal()
        try:
            with db.begin():
                session = get_session_for_update(db, session_id, user_id=user_id)
                question = (
                    get_question_for_session_for_update(db, session_id, question_id)
                    if session is not None
                    else None
                )
                if session is None or question is None:
                    raise AnswerClaimNotFound("Interview session not found")
                if question.status == QuestionStatus.EVALUATED.value:
                    return False
                if (
                    question.status == QuestionStatus.EVALUATING.value
                    and not self._is_stale(question.answer_submitted_at)
                ):
                    raise EvaluationPersistenceConflict("Evaluation is still in progress")
                if question.status not in (
                    QuestionStatus.EVALUATING.value,
                    QuestionStatus.EVALUATION_FAILED.value,
                ):
                    raise EvaluationPersistenceConflict("Question is not retryable")
                now = datetime.utcnow()
                update_session_state(
                    db, session, status=SessionStatus.IN_PROGRESS, updated_at=now
                )
                # Refresh the staleness lease so a concurrent worker sees this
                # retry as in-progress and backs off. Without this, the lease
                # kept the original (already-stale) answer_submitted_at, so a
                # second worker would immediately re-claim the same retry.
                update_question(
                    db,
                    question,
                    status=QuestionStatus.EVALUATING,
                    answer_submitted_at=now,
                )
                create_audit_event(
                    db,
                    session_id=session_id,
                    question_id=question_id,
                    event_type="EVALUATION_RETRY_STARTED",
                    question_number=question.question_number,
                    from_status=question.status,
                    to_status=QuestionStatus.EVALUATING,
                    created_at=now,
                )
                return True
        finally:
            db.close()

    @staticmethod
    def _evaluation_result(question) -> dict[str, Any]:
        return {
            "session_id": question.session_id,
            "question_id": question.id,
            "question_number": question.question_number,
            "status": question.status,
            "evaluation": question.evaluation,
            "next_question": None,
        }

    def generate_next_question(
        self,
        user_id: int,
        session_id: int,
        question_id: int,
    ) -> dict[str, Any]:
        """Generate and persist the next question from PostgreSQL state."""
        db = SessionLocal()
        try:
            with db.begin():
                session = get_session_for_update(db, session_id, user_id=user_id)
                if session is None:
                    raise AnswerClaimNotFound("Interview session not found")
                evaluated_question = get_question_for_session_for_update(
                    db, session_id, question_id
                )
                if evaluated_question is None:
                    raise GenerationConflict("Question not found for session")
                if evaluated_question.status != QuestionStatus.EVALUATED.value:
                    raise GenerationConflict("Question is not evaluated")
                retry_started = session.status in (
                    SessionStatus.GENERATING.value,
                    SessionStatus.GENERATION_FAILED.value,
                )
                if session.status == SessionStatus.COMPLETED.value:
                    raise GenerationConflict("Completed session cannot generate a question")
                if (
                    session.status == SessionStatus.GENERATING.value
                    and not self._is_stale(session.updated_at)
                ):
                    raise GenerationConflict("Question generation is still in progress")
                if session.status not in (
                    SessionStatus.IN_PROGRESS.value,
                    SessionStatus.GENERATING.value,
                    SessionStatus.GENERATION_FAILED.value,
                ):
                    raise GenerationConflict("Session cannot start question generation")

                questions = list_questions(db, session_id)
                evaluated_count = sum(
                    item.status == QuestionStatus.EVALUATED.value
                    for item in questions
                )
                next_number = max(
                    (item.question_number for item in questions if item.question_number is not None),
                    default=0,
                ) + 1
                existing_next = get_question_by_number(db, session_id, next_number)
                if existing_next is not None:
                    return self._next_question_result(existing_next)
                if evaluated_count >= 5 or next_number > 5:
                    now = datetime.utcnow()
                    update_session_state(
                        db, session, status=SessionStatus.READY_TO_FINISH, updated_at=now
                    )
                    create_audit_event(
                        db,
                        session_id=session_id,
                        question_id=question_id,
                        event_type="INTERVIEW_READY_TO_FINISH",
                        question_number=evaluated_question.question_number,
                        from_status=SessionStatus.IN_PROGRESS,
                        to_status=SessionStatus.READY_TO_FINISH,
                        created_at=now,
                    )
                    return {
                        "session_id": session_id,
                        "question_id": question_id,
                        "status": SessionStatus.READY_TO_FINISH.value,
                        "evaluation": evaluated_question.evaluation,
                        "next_question": None,
                    }

                next_difficulty = self._next_difficulty(evaluated_question)
                now = datetime.utcnow()
                update_session_state(
                    db, session, status=SessionStatus.GENERATING, updated_at=now
                )
                create_audit_event(
                    db,
                    session_id=session_id,
                    question_id=question_id,
                    event_type=(
                        "GENERATION_RETRY_STARTED"
                        if retry_started
                        else "GENERATION_STARTED"
                    ),
                    question_number=next_number,
                    from_status=SessionStatus.IN_PROGRESS,
                    to_status=SessionStatus.GENERATING,
                    details={"question_number": next_number},
                    created_at=now,
                )
                role = session.role
                current_difficulty = next_difficulty
        finally:
            db.rollback()
            db.close()

        try:
            generated_question = self._generate_question_text(
                user_id=user_id,
                role=role,
                difficulty=current_difficulty,
            )
            generated_question = self._validate_generated_question(generated_question)
        except Exception as exc:
            self._persist_generation_failure(
                user_id=user_id,
                session_id=session_id,
                question_id=question_id,
                question_number=next_number,
                error_type=type(exc).__name__,
                retry_started=retry_started,
            )
            raise

        db = SessionLocal()
        try:
            with db.begin():
                session = get_session_for_update(db, session_id, user_id=user_id)
                if session is None:
                    raise AnswerClaimNotFound("Interview session not found")
                if session.status != SessionStatus.GENERATING.value:
                    existing = get_question_by_number(db, session_id, next_number)
                    if existing is not None:
                        return self._next_question_result(existing)
                    raise GenerationConflict("Generation state changed before persistence")
                # Recompute the slot from the authoritative, locked state rather
                # than trusting the value snapshotted before the (slow) LLM call:
                # if a stale-lease concurrent generation advanced the interview
                # while we were calling the LLM, the pre-LLM number is stale.
                persisted_questions = list_questions(db, session_id)
                persist_number = max(
                    (
                        item.question_number
                        for item in persisted_questions
                        if item.question_number is not None
                    ),
                    default=0,
                ) + 1
                existing = get_question_by_number(db, session_id, persist_number)
                if existing is not None:
                    return self._next_question_result(existing)
                if persist_number > 5:
                    # The interview filled up while we were generating; do not
                    # persist an out-of-range question. A subsequent call
                    # transitions the session to READY_TO_FINISH.
                    raise GenerationConflict(
                        "Interview already has the maximum number of questions"
                    )

                question = create_question(
                    db,
                    session_id=session_id,
                    question=generated_question,
                    difficulty=current_difficulty,
                    question_number=persist_number,
                    status=QuestionStatus.ACTIVE,
                )
                now = datetime.utcnow()
                create_audit_event(
                    db,
                    session_id=session_id,
                    question_id=question.id,
                    event_type=(
                        "GENERATION_RETRY_SUCCEEDED"
                        if retry_started
                        else "GENERATION_SUCCEEDED"
                    ),
                    question_number=persist_number,
                    from_status=SessionStatus.GENERATING,
                    to_status=SessionStatus.IN_PROGRESS,
                    created_at=now,
                )
                update_session_state(
                    db, session, status=SessionStatus.IN_PROGRESS, updated_at=now
                )
                return self._next_question_result(question)
        except IntegrityError:
            # A concurrent generation won the race to persist the next
            # question (same number, or the single-active-question index).
            # Return that already-persisted active question instead of
            # surfacing a 500; if none is visible, report a retryable conflict.
            recovery_db = SessionLocal()
            try:
                active = get_current_question(recovery_db, session_id)
            finally:
                recovery_db.close()
            if active is not None:
                return self._next_question_result(active)
            raise GenerationConflict(
                "Concurrent question generation conflict"
            )
        finally:
            db.close()

    def _persist_generation_failure(
        self,
        user_id: int,
        session_id: int,
        question_id: int,
        question_number: int,
        error_type: str,
        retry_started: bool = False,
    ) -> None:
        db = SessionLocal()
        try:
            with db.begin():
                session = get_session_for_update(db, session_id, user_id=user_id)
                if session is None:
                    raise AnswerClaimNotFound("Interview session not found")
                if session.status != SessionStatus.GENERATING.value:
                    return
                now = datetime.utcnow()
                update_session_state(
                    db, session, status=SessionStatus.GENERATION_FAILED, updated_at=now
                )
                create_audit_event(
                    db,
                    session_id=session_id,
                    question_id=question_id,
                    event_type=(
                        "GENERATION_RETRY_FAILED"
                        if retry_started
                        else "GENERATION_FAILED"
                    ),
                    question_number=question_number,
                    from_status=SessionStatus.GENERATING,
                    to_status=SessionStatus.GENERATION_FAILED,
                    details={"error_type": error_type, "question_number": question_number},
                    created_at=now,
                )
        finally:
            db.close()

    def _generate_question_text(self, user_id: int, role: str, difficulty: int) -> str:
        """Use existing AI components without reading manager session state."""
        cv_path = self.manager.storage.get_active_cv(user_id)
        document = self.manager.parser.parse(
            file_path=cv_path, role="user", document_type="cv"
        )
        analysis = self.manager.analyzer.analyze(document.content)
        difficulty_label = self._difficulty_label(difficulty)
        query = self.manager.query_builder.build(analysis, role, difficulty_label)
        # Use isolated, per-request stores so a concurrent interview for another
        # user can never overwrite this user's CV/knowledge context mid-request.
        cv_store = self.manager.rag.ensure_cv_store(user_id, cv_path)
        knowledge_store = self.manager.rag.ensure_knowledge_store(role)
        results = self.manager.rag.retrieve_hybrid_isolated(
            query, cv_store=cv_store, knowledge_store=knowledge_store
        )
        prompt = self.manager.prompt_builder.build_question_prompt(
            role=role,
            difficulty=difficulty_label,
            cv_chunks=[item.chunk for item in results if item.chunk.role == "user"],
            knowledge_chunks=[item.chunk for item in results if item.chunk.role != "user"],
        )
        return self.manager.provider.generate_question(prompt)

    @staticmethod
    def _validate_generated_question(question: str) -> str:
        if not isinstance(question, str):
            raise ValueError("Generated question must be text")
        cleaned = question.strip()
        if not cleaned:
            raise ValueError("Generated question is empty")
        return cleaned

    @staticmethod
    def _next_difficulty(question) -> int:
        level = str((question.evaluation or {}).get("level", "medium")).lower()
        difficulty, _ = AdaptiveEngine.get_next_difficulty(level, int(question.difficulty))
        return difficulty

    @staticmethod
    def _difficulty_label(difficulty: int) -> str:
        if difficulty <= 2:
            return "easy"
        if difficulty >= 4:
            return "hard"
        return "medium"

    @staticmethod
    def _next_question_result(question) -> dict[str, Any]:
        return {
            "session_id": question.session_id,
            "question_id": question.id,
            "question_number": question.question_number,
            "status": question.status,
            "difficulty": question.difficulty,
            "next_question": question.question,
            "evaluation": None,
        }

    def finish_interview(self, user_id: int, session_id: int) -> dict[str, Any]:
        """Persist the durable READY_TO_FINISH -> COMPLETED transition.

        PostgreSQL is the source of truth. The final score/recommendation are
        computed deterministically from persisted evaluations; InterviewManager
        is never consulted as workflow state. The service owns the transaction
        and commits the state transition, score/recommendation, and
        INTERVIEW_COMPLETED audit event together; any failure rolls back.
        """
        db = SessionLocal()
        try:
            with db.begin():
                session = get_session_for_update(db, session_id)
                if session is None:
                    raise FinishNotFoundError(
                        f"Interview session {session_id} not found"
                    )
                # Ownership is enforced before any state change.
                if session.user_id != user_id:
                    raise FinishForbidden(
                        "You do not own this interview session"
                    )

                # Idempotent completion: return the persisted result without
                # recalculating the score/recommendation or writing a duplicate
                # audit event.
                if session.status == SessionStatus.COMPLETED.value:
                    return self._finish_result_from_persisted(
                        session, db, session_id
                    )

                if session.status != SessionStatus.READY_TO_FINISH.value:
                    raise FinishConflict(
                        f"Cannot finish interview in status {session.status}"
                    )

                questions = list_questions(db, session_id)
                final_score, recommendation, evaluated_count = (
                    self._compute_final_result(questions)
                )
                finished_at = datetime.utcnow()
                update_session_state(
                    db,
                    session,
                    status=SessionStatus.COMPLETED,
                    overall_score=final_score,
                    recommendation=recommendation,
                    finished_at=finished_at,
                    updated_at=finished_at,
                )
                create_audit_event(
                    db,
                    session_id=session_id,
                    question_id=None,
                    event_type="INTERVIEW_COMPLETED",
                    from_status=SessionStatus.READY_TO_FINISH,
                    to_status=SessionStatus.COMPLETED,
                    details={
                        "question_count": evaluated_count,
                        "overall_score": final_score,
                    },
                    created_at=finished_at,
                )
                return {
                    "session_id": session_id,
                    "status": SessionStatus.COMPLETED.value,
                    "overall_score": final_score,
                    "recommendation": recommendation,
                    "finished_at": finished_at,
                    "questions_evaluated": evaluated_count,
                }
        finally:
            db.close()

    @staticmethod
    def _compute_final_result(questions: list) -> tuple[float, str, int]:
        """Derive the final score/recommendation from persisted evaluations only.

        Only questions with a non-null ``question_number`` (the 1..5 canonical
        range enforced by the schema CHECK) and ``EVALUATED`` status participate.
        Legacy/archived rows with ``question_number IS NULL`` are ignored, so
        they cannot influence the final result.
        """
        valid = [
            q
            for q in questions
            if q.question_number is not None
            and q.status == QuestionStatus.EVALUATED.value
        ]
        numbers = sorted({q.question_number for q in valid})
        if numbers != [1, 2, 3, 4, 5]:
            raise FinishConflict(
                "Interview must have five evaluated questions to finish"
            )
        scores = [float(q.score) for q in valid if q.score is not None]
        if len(scores) != 5:
            raise FinishConflict(
                "Interview must have five evaluated questions to finish"
            )
        final_score = round(sum(scores) / len(scores), 1)
        recommendation = InterviewService._recommendation_for_score(final_score)
        return final_score, recommendation, len(valid)

    @staticmethod
    def _recommendation_for_score(final_score: float) -> str:
        """Pure recommendation tiers derived from the persisted final score."""
        if final_score >= 9:
            return "Strong Hire"
        if final_score >= 6:
            return "Hire"
        if final_score >= 4:
            return "Hold"
        return "Reject"

    @staticmethod
    def _finish_result_from_persisted(session, db: Session, session_id: int) -> dict[str, Any]:
        """Build the completion result from already-persisted state (idempotent)."""
        questions = list_questions(db, session_id)
        validated = [
            q
            for q in questions
            if q.question_number is not None
            and q.status == QuestionStatus.EVALUATED.value
        ]
        return {
            "session_id": session.id,
            "status": session.status,
            "overall_score": session.overall_score,
            "recommendation": session.recommendation,
            "finished_at": session.finished_at,
            "questions_evaluated": len(validated),
        }
