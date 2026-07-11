from sqlalchemy.orm import Session

from models import (
    InterviewQuestion,
    InterviewSession,
    User,
)
from models import InterviewSession
from datetime import datetime

def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    return (
        db.query(User)
        .filter(User.email == email)
        .first()
    )


def create_user(
    db: Session,
    name: str,
    email: str,
    hashed_password: str,
) -> User:

    user = User(
        name=name,
        email=email,
        hashed_password=hashed_password,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def get_user_by_id(
    db: Session,
    user_id: int,
) -> User | None:

    return (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )   

def create_interview_session(
    db: Session,
    user_id: int,
    role: str,
) -> InterviewSession:

    session = InterviewSession(
        user_id=user_id,
        role=role,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session

# def create_interview_question(
#     db: Session,
#     session_id: int,
#     question: str,
#     answer: str,
#     score: float,
#     feedback: str,
#     difficulty: int,
# ) -> InterviewQuestion:

#     interview_question = InterviewQuestion(
#         session_id=session_id,
#         question=question,
#         answer=answer,
#         score=score,
#         feedback=feedback,
#         difficulty=difficulty,
#     )

#     db.add(interview_question)
#     db.commit()
#     db.refresh(interview_question)

#     return interview_question

def create_question(
    db: Session,
    session_id: int,
    question: str,
    difficulty: int,
) -> InterviewQuestion:

    obj = InterviewQuestion(
        session_id=session_id,
        question=question,
        difficulty=difficulty,
    )

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj

def get_question_by_id(
    db: Session,
    question_id: int,
) -> InterviewQuestion | None:

    return (
        db.query(InterviewQuestion)
        .filter(
            InterviewQuestion.id == question_id
        )
        .first()
    )

def update_question_result(
    db: Session,
    question: InterviewQuestion,
    answer: str,
    score: float,
    feedback: str,
):

    question.answer = answer
    question.score = score
    question.feedback = feedback

    db.commit()
    db.refresh(question)

    return question

def get_session_by_id(
    db: Session,
    session_id: int,
) -> InterviewSession | None:

    return (
        db.query(InterviewSession)
        .filter(
            InterviewSession.id == session_id
        )
        .first()
    )


def finish_interview_session(
    db: Session,
    session: InterviewSession,
    overall_score: float,
    recommendation: str,
):

    session.overall_score = overall_score
    session.recommendation = recommendation
    session.status = "completed"
    session.finished_at = datetime.utcnow()

    db.commit()
    db.refresh(session)

    return session

def get_questions_by_session(
    db: Session,
    session_id: int,
) -> list[InterviewQuestion]:

    return (
        db.query(InterviewQuestion)
        .filter(
            InterviewQuestion.session_id == session_id
        )
        .all()
    )

def get_sessions_by_user(
    db: Session,
    user_id: int,
) -> list[InterviewSession]:

    return (
        db.query(InterviewSession)
        .filter(
            InterviewSession.user_id == user_id
        )
        .order_by(
            InterviewSession.started_at.desc()
        )
        .all()
    )

def get_session_with_questions(
    db: Session,
    session_id: int,
) -> InterviewSession | None:

    return (
        db.query(InterviewSession)
        .filter(
            InterviewSession.id == session_id
        )
        .first()
    )