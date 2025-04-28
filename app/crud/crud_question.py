from sqlalchemy.orm import Session
from backend.app.db.models import Question
import uuid
from datetime import datetime
from typing import List


def question_exists(db: Session, question_text: str) -> bool:
    """Check if a question with the same text already exists in the database."""
    existing_question = db.query(Question).filter(Question.question_text == question_text).first()
    return existing_question is not None


def create_question(db: Session, question_data: dict, created_by: str = None) -> Question:
    # Check if question already exists
    if question_exists(db, question_data["question_text"]):
        # Return existing question or None depending on your preference
        return db.query(Question).filter(Question.question_text == question_data["question_text"]).first()
    
    # If question doesn't exist, create a new one
    question = Question(
        id=uuid.uuid4(),
        hash=str(uuid.uuid4()),
        question_text=question_data["question_text"],
        option_a=question_data["option_a"],
        option_b=question_data["option_b"],
        option_c=question_data["option_c"],
        option_d=question_data["option_d"],
        correct_answer=question_data["correct_answer"],
        explanation=question_data["explanation"],
        topic=question_data.get("topic", ""),
        difficulty=question_data.get("difficulty",""),
        company=question_data.get("company", ""),
        created_by=created_by,
        created_at=datetime.utcnow()
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def get_questions_by_ids(db: Session, question_ids: List[uuid.UUID]) -> List[Question]:
    questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
    return questions
