from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from backend.app.db.models import QuizSession, QuizSessionQuestion, Question
from backend.app.db.session import get_db
from backend.app.api.deps import get_current_user
from backend.app.schemas.quiz_session import QuizSessionCreate, QuizSessionResponse
import uuid
from datetime import datetime
from backend.app.crud import crud_quiz

router = APIRouter(prefix="/quiz-sessions", tags=["Quiz Sessions"])


@router.post("/create", response_model=QuizSessionResponse)
def create_quiz_session(
    session_data: QuizSessionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    session = crud_quiz.create_quiz_session(db, current_user.id, session_data)
    return session

@router.get("/{session_id}", response_model=QuizSessionResponse)
def get_quiz_session(session_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    session = db.query(QuizSession).filter(QuizSession.id == session_id, QuizSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Quiz session not found")
    return session

