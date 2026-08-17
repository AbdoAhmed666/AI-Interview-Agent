"""Service layer for interview startup workflow."""

from typing import Any

try:
    from ..interview.interview_manager import InterviewManager
except ImportError:  # pragma: no cover - fallback for direct execution
    from interview.interview_manager import InterviewManager

from database import SessionLocal
from crud import (
    create_interview_session,
    create_question,
    update_question_result,
    finish_interview_session,
)


class InterviewService:
    """Coordinate the interview workflow and persist sessions/questions to the DB.

    This service keeps the adaptive InterviewManager in-memory for live interviews
    but stores authoritative records in the database. It maps manager IDs to DB IDs.
    """

    _shared_manager: InterviewManager | None = None

    def __init__(self) -> None:
        if InterviewService._shared_manager is None:
            InterviewService._shared_manager = InterviewManager()
        self.manager = InterviewService._shared_manager

        # mappings between in-memory manager ids and persistent DB ids
        self._manager_to_db: dict[int, int] = {}
        self._db_to_manager: dict[int, int] = {}
        self._manager_q_to_db_q: dict[int, int] = {}
        self._db_q_to_manager_q: dict[int, int] = {}

    def start_interview(self, user_id: int, role: str) -> dict[str, Any]:
        """Start an interview using the adaptive manager and persist a DB session/question.

        Returns a payload where `session_id` and `question_id` are the database ids
        which the frontend should use for subsequent requests.
        """
        import logging

        logger = logging.getLogger("interview.service")

        result = self.manager.start_interview(
            user_id=user_id,
            role=role,
        )

        logger.debug(
            "manager.start_interview result=%s",
            result,
        )

        # If the role is not compatible with the user's CV,
        # return the eligibility result without creating a DB session/question.
        if result.get("eligible") is False:
            return result

        manager_session_id = result.get("session_id")
        manager_question_id = result.get("question_id")
        first_question = result.get("question") or result.get("first_question")
        difficulty = result.get("difficulty") or 3

        logger.debug(
            "resolved first_question=%r",
            first_question,
        )

        # Safety checks before writing to the database.
        if manager_session_id is None:
            raise RuntimeError(
                "Interview manager did not return a session_id"
            )

        if manager_question_id is None:
            raise RuntimeError(
                "Interview manager did not return a question_id"
            )

        if not first_question:
            raise RuntimeError(
                "Interview manager did not return the first question"
            )

        db = SessionLocal()

        try:
            db_session = create_interview_session(
                db=db,
                user_id=user_id,
                role=role,
            )

            db_question = create_question(
                db=db,
                session_id=db_session.id,
                question=first_question,
                difficulty=int(difficulty),
            )

            # Store mappings between in-memory manager IDs
            # and persistent database IDs.
            self._manager_to_db[manager_session_id] = db_session.id
            self._db_to_manager[db_session.id] = manager_session_id

            self._manager_q_to_db_q[manager_question_id] = db_question.id
            self._db_q_to_manager_q[db_question.id] = manager_question_id

        finally:
            db.close()

        # Return DB IDs to the frontend.
        return {
            **result,
            "session_id": db_session.id,
            "question_id": db_question.id,
        }

    def submit_answer(self, user_id: int, session_id: int, question_id: int, answer: str) -> dict[str, Any]:
        """Persist the answer/evaluation and ask the manager to produce the next question.

        The `session_id` and `question_id` passed in are expected to be DB ids.
        """
        # translate DB ids to manager ids
        manager_session_id = self._db_to_manager.get(session_id)
        manager_question_id = self._db_q_to_manager_q.get(question_id)

        if manager_session_id is None or manager_question_id is None:
            raise KeyError("Unknown session or question id")

        result = self.manager.submit_answer(user_id=user_id, session_id=manager_session_id, question_id=manager_question_id, answer=answer)

        evaluation = result.get("evaluation")
        new_manager_question_id = result.get("question_id")
        next_question = result.get("next_question")
        next_difficulty = result.get("difficulty")

        db = SessionLocal()
        try:
            # update the answered question in DB
            update_question_result(db=db, question=self._db_get_question_obj(db, question_id), answer=answer, score=float(evaluation.get("score", 0)), feedback=evaluation.get("feedback", ""))

            # persist the newly generated next question
            db_new_q = create_question(db=db, session_id=session_id, question=next_question, difficulty=int(next_difficulty or 3))

            # map manager <-> db question ids
            if new_manager_question_id is not None:
                self._manager_q_to_db_q[new_manager_question_id] = db_new_q.id
                self._db_q_to_manager_q[db_new_q.id] = new_manager_question_id

        finally:
            db.close()

        # translate response ids back to DB ids for the client
        resp = dict(result)
        resp["question_id"] = db_new_q.id
        resp["session_id"] = session_id
        return resp

    def finish_interview(self, session_id: int) -> dict[str, Any]:
        """Finish the interview in the manager, then persist final score/recommendation to DB."""
        manager_session_id = self._db_to_manager.get(session_id)
        if manager_session_id is None:
            raise KeyError("Unknown session id")

        result = self.manager.finish_interview(session_id=manager_session_id)

        overall_score = float(result.get("final_score", 0))
        recommendation = result.get("recommendation", "")

        db = SessionLocal()
        try:
            session = finish_interview_session(db=db, session=self._db_get_session_obj(db, session_id), overall_score=overall_score, recommendation=recommendation)
        finally:
            db.close()

        return result

    def _db_get_question_obj(self, db, question_id: int):
        # helper to fetch question ORM object by id
        from crud import get_question_by_id

        return get_question_by_id(db, question_id)

    def _db_get_session_obj(self, db, session_id: int):
        from crud import get_session_by_id

        return get_session_by_id(db, session_id)
