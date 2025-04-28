from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
from backend.app.db.models import resume
from backend.app.services.quiz_generator_resume import generate_quiz
from backend.app.crud import crud_question
from backend.app.db.models import Question
from uuid import UUID
from backend.app.schemas.prompt import ResumePromptRequest
from pydantic import BaseModel
from backend.app.db.session import get_db
from backend.app.api.deps import get_current_user
from datetime import datetime
import os
import fitz  # PDF
import docx  # Word

UPLOAD_DIR = "upload"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/quiz-resume", tags=["Quiz Resume"])

def extract_text(file_path: str) -> str:
    if file_path.endswith(".pdf"):
        with fitz.Document(file_path) as doc:
            return "".join([page.get_text() for page in doc])
    elif file_path.endswith((".doc", ".docx")):
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        raise ValueError("Unsupported file type")

@router.post("/upload-file")
def upload_resume_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".doc", ".docx"]:
        raise HTTPException(status_code=400, detail="Invalid file type.")

    filename = f"{uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    try:
        content = extract_text(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract text: {e}")

    new_resume = resume(
        id=uuid4(),
        user_id=current_user.id,
        filename=file.filename,
        file_url=file_path,
        content=content,
        uploaded_at=datetime.utcnow()
    )
    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)
    return {"message": "Resume uploaded successfully", "resume_id": str(new_resume.id)}

  # e.g., "Generate 10 questions for a backend engineer interview"

@router.post("/generate-from-resume")
def generate_questions_from_resume_input(
    data: ResumePromptRequest,
    db: Session = Depends(get_db)
):
    # Fetch resume content
    resume_entry = db.query(resume).filter(resume.id == data.resume_id).first()
    if not resume_entry:
        raise HTTPException(status_code=404, detail="Resume not found")
    if not resume_entry.content:
        raise HTTPException(status_code=400, detail="Resume content is empty")

    # Prepare prompt for LLM
    combined_prompt = f"{data.user_prompt}\n\nResume Content:\n{resume_entry.content[:5000]}"

    try:
        # Generate quiz questions using Gemini
        questions = generate_quiz(combined_prompt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Gemini error: {str(e)}")

    created_questions = []
    existing_questions = []

    for q in questions:
        # Ensure all necessary keys
        q["company"] = q.get("company", "Unknown")
        q["topic"] = q.get("topic", "Resume")
        q["difficulty"] = q.get("difficulty", "Medium")

        # Avoid duplicates
        existing_q = db.query(Question).filter(Question.question_text == q["question_text"]).first()
        if existing_q:
            existing_questions.append(str(existing_q.id))
        else:
            created = crud_question.create_question(db, q)
            created_questions.append(str(created.id))

    return {
        "message": "✅ Questions generated from resume successfully!",
        "prompt": data.user_prompt,
        "new_questions": len(created_questions),
        "existing_questions": len(existing_questions),
        "ids": created_questions + existing_questions,
    }