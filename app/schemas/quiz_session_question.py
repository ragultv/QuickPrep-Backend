from pydantic import BaseModel
from uuid import UUID


class QuizSessionQuestionCreate(BaseModel):
    quiz_session_id: UUID
    question_id: UUID
    question_order: int


class QuizSessionQuestionResponse(QuizSessionQuestionCreate):
    id: UUID

    class Config:
        from_attributes = True
