from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    class Config:
        from_attributes = True

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str
    class Config:
        from_attributes = True

class UserSessionResponse(BaseModel):
    session_id: str
    score: float
    topic: str
    num_questions: int
    time_taken :str
    difficulty: str

class UserStatsResponse(BaseModel):
    total_quiz: int
    best_score: float

class UsernameAvailability(BaseModel):
    available: bool

class EmailVerificationRequest(BaseModel):
    email: EmailStr
    otp: str

class EmailSchema(BaseModel):
    email: str
