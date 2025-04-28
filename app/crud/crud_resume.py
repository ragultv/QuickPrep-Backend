from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException       
from uuid import UUID, uuid4
from app.db.models import resume
from app.db.session import get_db
from app.api.deps import get_current_user
from app.schemas.quiz_resume import ResumeUpload, ResumeResponse
from datetime import datetime

def add_resume(db: Session, user_id: UUID, resume_data: ResumeUpload) -> ResumeResponse:
    """
    Adds a new resume entry to the database.
    """
    # Check if the user already has a resume uploaded
    existing_resume = db.query(resume).filter(resume.user_id == user_id).first()
    if existing_resume:
        raise HTTPException(status_code=400, detail="Resume already uploaded")

    # Create a new resume entry in the database
    new_resume = resume(
        id=uuid4(),
        user_id=user_id,
        filename=resume_data.filename,
        file_url=resume_data.file_url,
        content=resume_data.content,  # Assuming content is not provided during upload
        uploaded_at=datetime.utcnow()
    )
    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)
    return new_resume

def add_content(db: Session, resume_id: UUID, content: str) -> ResumeResponse:
    """
    Adds content to an existing resume entry in the database.
    """
    # Fetch the existing resume entry
    existing_resume = db.query(resume).filter(resume.id == resume_id).first()
    if not existing_resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Update the content of the existing resume entry
    existing_resume.content = content
    db.commit()
    db.refresh(existing_resume)
    return existing_resume
