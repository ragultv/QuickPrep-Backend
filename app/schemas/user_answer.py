from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List

class SingleAnswer(BaseModel):
    question_id: UUID
    selected_option: str

class UserAnswerCreate(BaseModel):
    quiz_session_id: UUID
    question_id: UUID
    selected_option: str

class AnswerSubmission(BaseModel):
    quiz_session_id: UUID
    answers: List[SingleAnswer]

class AnswerResponse(BaseModel):
    question_id: UUID
    selected_option: str
    is_correct: bool
    answered_at: datetime

    class Config:
        from_attributes = True
class UserSessionResponse(BaseModel):
    session_id: str
    score: int
    topic: str

class UserStatsResponse(BaseModel):
    total_quiz_sessions: int
    total_score: int
    average_score: float