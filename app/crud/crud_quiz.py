from sqlalchemy.orm import Session
from backend.app.db.models import QuizSession, QuizSessionQuestion, UserAnswer
from backend.app.schemas.quiz_session import QuizSessionCreate
from backend.app.schemas.user_answer import UserAnswerCreate
import uuid
from datetime import datetime
from typing import List
from uuid import UUID


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
        started_at=datetime.utcnow(),
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
