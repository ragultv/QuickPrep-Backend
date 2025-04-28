from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class QuestionBase(BaseModel):
    hash: str
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str
    explanation: str
    topic: str | None = None
    difficulty: str | None = None
    company: str | None = None

class QuestionCreate(QuestionBase):
    created_by: UUID | None = None
    

class QuestionResponse(QuestionBase):
    id: UUID
    created_by: UUID | None = None
    created_at: datetime

    class Config:
        from_attributes = True
