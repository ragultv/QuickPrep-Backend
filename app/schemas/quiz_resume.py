from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import UploadFile

class ResumeUpload(BaseModel):
    filename: str
    file_url: str
    content :str  # URL after upload

class ResumeResponse(BaseModel):
    id: UUID
    user_id: UUID
    filename: str
    file_url: str
    content: Optional[str]
    uploaded_at: datetime

    class Config:
        orm_mode = True

class ResumeUploadRequest:
    file: UploadFile