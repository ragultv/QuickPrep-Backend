from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_user
from app.db.models import User, QuizSession  # Assuming QuizSession is the model for quiz sessions
from typing import List
from datetime import timedelta
from pydantic import BaseModel
from app.schemas.user import UserSessionResponse ,UserStatsResponse # Assuming you have a schema for user session response



router = APIRouter(prefix="/user_stats", tags=["User Stats"])

def format_duration(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}m {seconds}s" if minutes else f"{seconds}s"

@router.get("/recent_sessions", response_model=List[UserSessionResponse])
def get_recent_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Fetch user's recent quiz sessions
    recent_sessions = (
        db.query(QuizSession)
        .filter(
            QuizSession.user_id == current_user.id,
            QuizSession.submitted_at.isnot(None)
        )
        .order_by(QuizSession.submitted_at.desc())
        .limit(5)
        .all()
    )
    
    # if not recent_sessions:
    #     raise HTTPException(status_code=200, detail="No recent sessions found")

    return [
        UserSessionResponse(
        session_id=str(session.id),
        num_questions=session.num_questions,
        time_taken=format_duration((session.submitted_at - session.started_at) if (session.submitted_at and session.started_at) else timedelta(0)),
        score=(session.score / session.num_questions * 100) if session.num_questions else 0,
        topic=session.topic,
        difficulty=session.difficulty
    )
        for session in recent_sessions
    ]

@router.get("/history", response_model=List[UserSessionResponse])
def get_quiz_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Fetch user's quiz sessions
    previous_sessions = (
        db.query(QuizSession)
        .filter(
            QuizSession.user_id == current_user.id,
            QuizSession.submitted_at.isnot(None)
        )
        .order_by(QuizSession.submitted_at.desc())
        .all()
    )
    
    # if not previous_sessions:
    #     raise HTTPException(status_code=404, detail="No recent sessions found")

    return [
        UserSessionResponse(
        session_id=str(session.id),
        num_questions=session.num_questions,
        time_taken=format_duration((session.submitted_at - session.started_at) if (session.submitted_at and session.started_at) else timedelta(0)),
        score=(session.score / session.num_questions * 100) if session.num_questions else 0,
        topic=session.topic,
        difficulty=session.difficulty
    )
        for session in previous_sessions
    ]

@router.get("/top_subject", response_model=str)
def get_top_subject(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Fetch user's quiz sessions
    quiz_sessions = db.query(QuizSession).filter(QuizSession.user_id == current_user.id).all()
    
    if not quiz_sessions:
        raise HTTPException(status_code=404, detail="No quiz sessions found")

    # Count scores by topic
    topic_scores = {}
    for session in quiz_sessions:
        if session.topic in topic_scores:
            topic_scores[session.topic] += session.score
        else:
            topic_scores[session.topic] = session.score

    # Determine the top subject
    top_subject = max(topic_scores, key=topic_scores.get)
    
    return top_subject




    #average_time: float

@router.get("/my_stats", response_model=UserStatsResponse)
def get_user_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Fetch user's quiz sessions
    quiz_sessions = db.query(QuizSession).filter(QuizSession.user_id == current_user.id,QuizSession.submitted_at.isnot(None)).all()
    
    if not quiz_sessions:
        return UserStatsResponse(total_quiz=0, best_score=0)

    total_quiz = len(quiz_sessions)
    #average_time = sum((session.submitted_at - session.started_at).total_seconds() for session in quiz_sessions) / total_quiz
    best_score = max((session.score / session.num_questions) * 100 for session in quiz_sessions)
    best_score = round(best_score, 2)  # Optional: round to 2 decimal places

    
    return UserStatsResponse(
        total_quiz=total_quiz,
        #average_time=average_time,
        best_score=best_score
    )

@router.get("/{user_id}/stats", response_model=UserStatsResponse)
def get_stats_for_user(user_id: str, db: Session = Depends(get_db)):
    quiz_sessions = db.query(QuizSession).filter(QuizSession.user_id == user_id).all()
    if not quiz_sessions:
        return UserStatsResponse(total_quiz=0, best_score=0, top_subjects=[])
    total_quiz = len(quiz_sessions)
    best_score = max(session.score for session in quiz_sessions)
    # Calculate top subjects
    topic_scores = {}
    for session in quiz_sessions:
        if session.topic in topic_scores:
            topic_scores[session.topic] += session.score
        else:
            topic_scores[session.topic] = session.score
    top_subjects = sorted(topic_scores, key=topic_scores.get, reverse=True)[:3]
    return UserStatsResponse(
        total_quiz=total_quiz,
        best_score=best_score,
        top_subjects=top_subjects
    )
