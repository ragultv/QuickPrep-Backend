from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional,List


class QuizSessionCreate(BaseModel):
    prompt: str
    topic: str
    difficulty: str
    company: str
    question_ids: List[UUID]
   



class QuizSessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    prompt: str
    topic: Optional[str]
    difficulty: Optional[str]
    company: Optional[str]
    num_questions: int
    total_duration: float
    score: int
    started_at: datetime
    submitted_at: Optional[datetime]

    class Config:
        from_attributes = True
