from sqlalchemy.orm import Session
from uuid import uuid4, UUID
from datetime import datetime
import uuid

from app.db.models import (
    QuizSession,
    QuizSessionQuestion,
    UserAnswer,
    HostedQuizSession,
    HostedQuizSessionQuestion,
    HostedSession,
    HostedSessionParticipant
)
from app.schemas.quiz_session import QuizSessionCreate, HostedSessionCreate
from app.schemas.user_answer import UserAnswerCreate


def create_quiz_session(db: Session, user_id: UUID, session_data: QuizSessionCreate):

    num_questions=len(session_data.question_ids)
    duration_minutes = round(num_questions * 1.5, 2)

    session = QuizSession(
        id=uuid.uuid4(),
        user_id=user_id,
        prompt=session_data.prompt,
        topic=session_data.topic,
        difficulty=session_data.difficulty,
        company=session_data.company,
        num_questions=num_questions,
        total_duration=duration_minutes,
        started_at=None,
        submitted_at=None
    )
    db.add(session)
    db.flush()  # So we get session.id

    for idx, qid in enumerate(session_data.question_ids):
        session_question = QuizSessionQuestion(
            id=uuid.uuid4(),
            quiz_session_id=session.id,
            question_id=qid,
            question_order=idx + 1,
        )
        db.add(session_question)

    db.commit()
    db.refresh(session)
    return session



def add_question_to_session(db: Session, quiz_session_id: str, question_id: str, order: int):
    """
    (Optional helper) Link a single Question to a QuizSession.
    """
    qsq = QuizSessionQuestion(
        id=uuid.uuid4(),
        quiz_session_id=quiz_session_id,
        question_id=question_id,
        question_order=order
    )
    db.add(qsq)
    db.commit()
    db.refresh(qsq)
    return qsq


def submit_answer(db: Session, answer_data: UserAnswerCreate):
    """
    Store a UserAnswer for a QuizSession.
    """
    answer = UserAnswer(
        id=uuid.uuid4(),
        quiz_session_id=answer_data.quiz_session_id,
        question_id=answer_data.question_id,
        selected_option=answer_data.answer,
        is_correct=answer_data.is_correct,
        answered_at=datetime.utcnow()
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return answer

def create_hosted_session(
    db: Session,
    host_id: UUID,
    data: HostedSessionCreate
) -> HostedSession:
    # 1. create standalone quiz
    hqs = HostedQuizSession(
        id=uuid4(),
        host_id=host_id,
        prompt=data.prompt,
        topic=data.topic,
        difficulty=data.difficulty,
        company=data.company,
        num_questions=len(data.question_ids),
        total_duration=data.total_duration,
        created_at=datetime.utcnow()
    )
    db.add(hqs)
    db.flush()

    # 2. link questions
    for idx, qid in enumerate(data.question_ids, start=1):
        db.add(HostedQuizSessionQuestion(
            id=uuid4(),
            hosted_session_id=hqs.id,
            question_id=qid,
            question_order=idx
        ))

    # 3. create live room
    hs = HostedSession(
        id=uuid4(),
        quiz_session_id=hqs.id,
        host_id=host_id,
        title=data.title,
        total_spots=data.total_spots,
        current_participants=0,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(hs)
    db.commit()
    db.refresh(hs)
    return hs


def get_hosted_session(db: Session, hosted_session_id: UUID):
    """
    Get a hosted session by ID.
    """
    return db.query(HostedSession).filter(HostedSession.id == hosted_session_id).first()

def get_active_hosted_sessions(db: Session, skip: int = 0, limit: int = 100):
    """
    Get all active hosted sessions.
    """
    return db.query(HostedSession).filter(HostedSession.is_active == True).offset(skip).limit(limit).all()

def join_hosted_session(db: Session, hosted_session_id: UUID, user_id: UUID):
    """
    Join a hosted session.
    """
    hosted_session = get_hosted_session(db, hosted_session_id)
    if not hosted_session:
        raise ValueError("Hosted session not found")
    if not hosted_session.is_active:
        raise ValueError("Session is not active")
    if hosted_session.current_participants >= hosted_session.total_spots:
        raise ValueError("Session is full")

    # Check if already joined
    existing = db.query(HostedSessionParticipant).filter_by(
        user_id=user_id, hosted_session_id=hosted_session_id
    ).first()
    if existing:
        return hosted_session  # Already joined

    # Add participant
    participant = HostedSessionParticipant(
        user_id=user_id, hosted_session_id=hosted_session_id
    )
    db.add(participant)
    hosted_session.current_participants += 1
    db.commit()
    db.refresh(hosted_session)
    return hosted_session
