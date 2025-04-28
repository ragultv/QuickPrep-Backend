from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.services.quiz_generator import generate_large_quiz
from backend.app.crud import crud_question
from backend.app.db.models import Question
from pydantic import BaseModel
from typing import List
from backend.app.db.models import PromptResponse
from backend.app.services.quiz_generator import clean_markdown_json  # <-- IMPORT CLEANER
import re
import uuid
import json
from backend.app.schemas.prompt import PromptRequest  # Assuming you have a schema for the prompt request
from fastapi_cache.decorator import cache
from backend.app.services.prompt_echancer import get_gemini_response  # Assuming you have a function to enhance prompts
import logger



router = APIRouter()
  # Add if not imported


@router.post("/prompt_enhancer")
async def enhance_prompt(payload: PromptRequest, db: Session = Depends(get_db)):
    """
    Enhance user prompts for quiz generation using AI model
    """
    try:
        # Get enhanced prompt from Gemini
        enhanced_prompt = get_gemini_response(payload.prompt)
        
        # Check for error responses from Gemini
        if enhanced_prompt.startswith("❌"):
            raise HTTPException(status_code=500, detail=enhanced_prompt)
        
        # Here you could add database logging if needed
        # Example: db.add(PromptLog(original=payload.prompt, enhanced=enhanced_prompt))
        # db.commit()
        
        return {"enhanced_prompt": enhanced_prompt}
        
    except HTTPException as he:
        # Re-raise known HTTP exceptions
        raise he
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error enhancing prompt: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during prompt enhancement"
        )
@router.post("/generate/")
@cache(expire=3600)  # Cache for 1 hour
async def generate_and_save_questions(payload: PromptRequest, db: Session = Depends(get_db)):
    try:
        # Extract exact number from prompt using regex
        match = re.search(r'\b(\d+)\b', payload.prompt)
        total_questions = int(match.group(1)) if match else 30
        
        # Enforce minimum/maximum bounds
        total_questions = max(5, min(total_questions, 10000))
        
        # Dynamic batch sizing
        batch_size = min(20, total_questions)  # Never exceed requested total
        
        questions = generate_large_quiz(
            payload.prompt, 
            total_questions=total_questions,
            batch_size=batch_size
        )
        
        # Final count validation
        if len(questions) != total_questions:
            raise ValueError(f"Generated {len(questions)} instead of {total_questions} questions")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate quiz: {str(e)}")

    created_questions = []
    existing_questions = []

    for q in questions:
        if "question_text" not in q:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid question format: missing question_text in {q}"
            )
        q["company"] = q.get("company", "Unknown")
        q["topic"] = q.get("topic", "General")
        q["difficulty"] = q.get("difficulty", "Easy")

        existing = db.query(Question).filter(Question.question_text == q["question_text"]).first()
        if existing:
            existing_questions.append(str(existing.id))
        else:
            created = crud_question.create_question(db, q)
            created_questions.append(str(created.id))

    all_question_ids = created_questions + existing_questions

    # 🚀 Save prompt and clean FULL response for fine-tuning later
    try:
        db.add(PromptResponse(prompt=payload.prompt, response=questions))
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save prompt/response: {str(e)}")

    return {
        "message": "Questions processed successfully!",
        "new_questions": len(created_questions),
        "existing_questions": len(existing_questions),
        "prompt": payload.prompt,
        "topics": [q["topic"] for q in questions],
        "difficulties": [q["difficulty"] for q in questions],
        "companies": [q["company"] for q in questions],
        "ids": all_question_ids
    }

@router.get("/{question_ids}")
def get_questions(question_ids: str, db: Session = Depends(get_db)):
    try:
        # Convert comma-separated string of IDs to list of UUIDs
        ids = [uuid.UUID(id.strip()) for id in question_ids.split(',')]

        # Fetch questions from database
        questions = crud_question.get_questions_by_ids(db, ids)

        # Instead of 404, return only found ones
        if not questions:
            return []  # ⬅️ Return empty list if none found

        # Transform for frontend
        transformed_questions = []
        for q in questions:
            transformed_questions.append({
                "id": str(q.id),
                "question": q.question_text,
                "options": [
                    q.option_a,
                    q.option_b,
                    q.option_c,
                    q.option_d
                ],
                "correctAnswer": q.correct_answer.upper(),
                "explanation": q.explanation
            })

        return transformed_questions
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid question IDs format")
