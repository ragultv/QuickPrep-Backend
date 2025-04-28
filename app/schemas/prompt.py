from pydantic import BaseModel, Field
from uuid import UUID

class PromptRequest(BaseModel):
    prompt: str

class PromptResponseRequest(BaseModel):
    prompt: str
    response: dict


class ResumePromptRequest(BaseModel):
    resume_id: UUID
    user_prompt: str