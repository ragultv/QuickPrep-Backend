# backend/app/api/routes/quiz_results.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel
from app.db.session import get_db
from app.api.deps import get_current_user
from app.db.models import QuizSession, UserAnswer, Question, JoinedQuizSession, JoinedUserAnswer
from app.schemas.quiz_result import QuizResultResponse, QuestionResult

router = APIRouter(prefix="/quiz-results", tags=["Quiz Results"])


@router.get("/{session_id}", response_model=QuizResultResponse)
def get_quiz_results(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Fetch session and verify ownership
    session = (
        db.query(QuizSession)
        .filter(QuizSession.id == session_id, QuizSession.user_id == current_user.id)
        .first()
    )
    if session and session.submitted_at:
        # Fetch all answers & include the question relationship
        answers = (
            db.query(UserAnswer)
            .filter(UserAnswer.quiz_session_id == session_id)
            .all()
        )
        # Build response list
        results = []
        for ua in answers:
            q: Question = ua.question  # relationship from UserAnswer → Question
            results.append(QuestionResult(
                question_id=q.id,
                question=q.question_text,
                options=[q.option_a, q.option_b, q.option_c, q.option_d],
                selected_option=ua.selected_option,
                correct_answer=q.correct_answer,
                is_correct=ua.is_correct,
                explanation=q.explanation,
            ))
        return QuizResultResponse(
            questions=results,
            score=session.score,
            total_questions=session.num_questions,
        )

    # Try JoinedQuizSession for hosted participants
    joined_session = db.query(JoinedQuizSession).filter(
        JoinedQuizSession.id == session_id,
        JoinedQuizSession.user_id == current_user.id
    ).first()
    if joined_session and joined_session.submitted_at:
        answers = db.query(JoinedUserAnswer).filter(JoinedUserAnswer.joined_session_id == session_id).all()
        results = []
        for ua in answers:
            q: Question = ua.question  # relationship from JoinedUserAnswer → Question
            results.append(QuestionResult(
                question_id=q.id,
                question=q.question_text,
                options=[q.option_a, q.option_b, q.option_c, q.option_d],
                selected_option=ua.selected_option,
                correct_answer=q.correct_answer,
                is_correct=ua.is_correct,
                explanation=q.explanation,
            ))
        return QuizResultResponse(
            questions=results,
            score=joined_session.score,
            total_questions=joined_session.num_questions,
        )

    raise HTTPException(404, "Quiz session not found or not submitted")