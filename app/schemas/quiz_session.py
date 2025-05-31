from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List , Dict
from app.schemas.quiz_session_question import QuizSessionQuestionResponse
from app.core.base_config import BaseConfig

# --------------------
# PERSONAL QUIZ SESSION
# --------------------

class QuizSessionCreate(BaseModel):
    prompt: str
    topic: str
    difficulty: str
    company: str
    question_ids: List[UUID]


class QuizSessionResponse(BaseConfig):
    id: UUID
    user_id: UUID
    prompt: str
    topic: Optional[str]
    difficulty: Optional[str]
    company: Optional[str]
    num_questions: int
    total_duration: float
    score: int
    questions: List[QuizSessionQuestionResponse] = []
    started_at: Optional[datetime]
    submitted_at: Optional[datetime]

    class Config:
        from_attributes = True

class SessionsByDateResponse(BaseModel):
    sessions_by_date: Dict[str, int]

    class Config:
        from_attributes = True

# ----------------------------
# HOSTED STANDALONE QUIZ SETUP
# ----------------------------

class HostedSessionCreate(BaseModel):
    prompt: str
    topic: str
    difficulty: str
    company: str
    question_ids: List[UUID]
    total_duration: float
    title: str
    total_spots: int


class HostedSessionResponse(BaseConfig):
    id: UUID
    quiz_session_id: UUID  # points to HostedQuizSession
    host_id: UUID
    title: str
    total_spots: int
    current_participants: int
    is_active: bool
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]

    class Config:
        from_attributes = True


class QuizSessionSummary(BaseModel):
    id: UUID
    topic: Optional[str]
    difficulty: Optional[str]
    num_questions: int
    question_ids: List[UUID]


class HostedSessionWithQuizResponse(BaseModel):
    id: UUID
    quiz_session_id: UUID
    host_id: UUID
    title: str
    total_spots: int
    current_participants: int
    is_active: bool
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    quiz_session: Optional[QuizSessionSummary]

    class Config:
        form_attributes = True


class JoinHostedSessionResponse(BaseModel):
    message: str
    participant_quiz_session_id: UUID
    hosted_session_id: UUID
    is_live: bool

    class Config:
        from_attributes = True
