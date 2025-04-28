from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional

class QuestionResult(BaseModel):
    question_id: UUID
    question: str
    options: List[str]
    selected_option: str
    correct_answer: str
    is_correct: bool
    explanation: Optional[str]

class QuizResultResponse(BaseModel):
    questions: List[QuestionResult]
    score: int
    total_questions: int

    class Config:
        form_attributes = True