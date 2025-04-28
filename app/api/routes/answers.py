from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from backend.app.db.models import QuizSession, QuizSessionQuestion, Question, UserAnswer
from backend.app.db.session import get_db
from backend.app.api.deps import get_current_user
from backend.app.schemas.user_answer import AnswerSubmission, AnswerResponse
from datetime import datetime
import uuid
from typing import List

router = APIRouter(prefix="/answers", tags=["Answers"])

@router.post("/submit", response_model=dict)
def submit_answers(
    submission: AnswerSubmission,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    session = db.query(QuizSession).filter(
        QuizSession.id == submission.quiz_session_id,
        QuizSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Quiz session not found")

    if session.submitted_at:
        raise HTTPException(status_code=400, detail="Quiz already submitted")

    score = 0
    results = []

    for answer in submission.answers:
        question = db.query(Question).filter(Question.id == answer.question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail=f"Question not found: {answer.question_id}")

        # Convert correct_answer to a string if it's stored as a character code
        correct_answer_str = chr(question.correct_answer) if isinstance(question.correct_answer, int) else question.correct_answer

        #print(f"DEBUG >> Question ID: {answer.question_id}")
        #print(f"DEBUG >> Selected Option: {answer.selected_option.upper()}")
        #print(f"DEBUG >> Correct Answer: {correct_answer_str.upper()}")
        #print(f"DEBUG >> Explanation: {question.explanation}")

        is_correct = (answer.selected_option.upper() == correct_answer_str.upper())
        if is_correct:
            score += 1

        db_answer = UserAnswer(
            id=uuid.uuid4(),
            quiz_session_id=submission.quiz_session_id,
            question_id=answer.question_id,
            selected_option=answer.selected_option.upper(),
            is_correct=is_correct,
            answered_at=datetime.utcnow()
        )
        db.add(db_answer)

        # Collect results for the response
        results.append({
            "question_id": answer.question_id,
            "selected_option": answer.selected_option.upper(),
            "correct_answer": correct_answer_str.upper(),
            "is_correct": is_correct,
            "explanation": question.explanation
        })

    session.score = score
    session.submitted_at = datetime.utcnow()
    db.commit()

    return {
        "message": "Answers submitted successfully",
        "score": score,
        "total_questions": len(submission.answers),
        "correct_answers": score,
        "incorrect_answers": len(submission.answers) - score,
        "results": results  # Include detailed results
    }



@router.get("/session/{session_id}", response_model=List[AnswerResponse])
def get_user_answers(session_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    session = db.query(QuizSession).filter(
        QuizSession.id == session_id,
        QuizSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    answers = db.query(UserAnswer).filter(UserAnswer.quiz_session_id == session_id).all()
    return answers
