from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from uuid import UUID
from app.db.models import QuizSession, QuizSessionQuestion, Question, HostedSessionParticipant, HostedSession, User, HostedSessionLeaderboard
from app.db.session import get_db
from app.api.deps import get_current_user
from app.schemas.quiz_session import (
    QuizSessionCreate,
    QuizSessionResponse,
    HostedSessionCreate,
    HostedSessionResponse,
    HostedSessionWithQuizResponse,
    JoinHostedSessionResponse
)
from app.db.models import HostedQuizSession, HostedQuizSessionQuestion
import uuid
from datetime import datetime
from app.crud import crud_quiz
from typing import List, Optional

router = APIRouter(prefix="/quiz-sessions", tags=["Quiz Sessions"])


@router.post("/create", response_model=QuizSessionResponse)
async def create_quiz_session(
    session_data: QuizSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = crud_quiz.create_quiz_session(db, current_user.id, session_data)
    return session

@router.post(
    "/create-hosted",
    response_model=HostedSessionResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_hosted_session(
    payload: HostedSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session =crud_quiz.create_hosted_session(db, current_user.id, payload)
    return session


@router.get("/hosted", response_model=List[HostedSessionResponse])
async def get_user_hosted_sessions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all hosted sessions created by the current user.
    """
    hosted_sessions = db.query(HostedSession).filter(HostedSession.host_id == current_user.id).offset(skip).limit(limit).all()
    return hosted_sessions

@router.get("/", response_model=List[QuizSessionResponse])
async def get_unstarted_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sessions = (
        db.query(QuizSession)
        .filter(
            QuizSession.user_id == current_user.id,
            QuizSession.started_at.is_(None)
        )
        .order_by(QuizSession.created_at.desc())
        .all()
    )
    return sessions

# Define a Pydantic model for the augmented response
class HostedSessionDetailsResponse(HostedSessionWithQuizResponse):
    current_user_participant_quiz_session_id: Optional[UUID] = None

@router.get("/hosted/{hosted_session_id}", response_model=HostedSessionDetailsResponse)
async def get_hosted_session_details_with_participant_info(
    hosted_session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    hosted_session = crud_quiz.get_hosted_session(db, hosted_session_id)
    if not hosted_session:
        raise HTTPException(status_code=404, detail="Hosted session not found")

    quiz_session_model = db.query(HostedQuizSession).filter(HostedQuizSession.id == hosted_session.quiz_session_id).first()
    quiz_session_data = None
    if quiz_session_model:
        question_ids = [
            str(q.question_id)
            for q in db.query(HostedQuizSessionQuestion).filter(HostedQuizSessionQuestion.hosted_session_id == quiz_session_model.id).order_by(HostedQuizSessionQuestion.question_order).all()
        ]
        quiz_session_data = {
            "id": str(quiz_session_model.id),
            "topic": quiz_session_model.topic,
            "difficulty": quiz_session_model.difficulty,
            "num_questions": quiz_session_model.num_questions,
            "question_ids": question_ids,
        }

    # Convert hosted_session to a dictionary suitable for Pydantic model
    response_data = {
        "id": hosted_session.id,
        "host_id": hosted_session.host_id,
        "quiz_session_id": hosted_session.quiz_session_id,
        "title": hosted_session.title,
        "total_spots": hosted_session.total_spots,
        "current_participants": hosted_session.current_participants,
        "is_active": hosted_session.is_active,
        "created_at": hosted_session.created_at,
        "started_at": hosted_session.started_at,
        "ended_at": hosted_session.ended_at,
        "quiz_session": quiz_session_data,
        "current_user_participant_quiz_session_id": None
    }

    # Check if current_user is a participant and find their specific QuizSession id
    participant_record = db.query(HostedSessionParticipant).filter(
        HostedSessionParticipant.hosted_session_id == hosted_session_id,
        HostedSessionParticipant.user_id == current_user.id
    ).first()

    if participant_record and quiz_session_model:
        # Find the QuizSession created for this participant for this specific hosted quiz content
        participant_quiz_session = db.query(QuizSession).filter(
            QuizSession.user_id == current_user.id,
            QuizSession.prompt == quiz_session_model.prompt,
            QuizSession.topic == quiz_session_model.topic,
            QuizSession.difficulty == quiz_session_model.difficulty,
        ).order_by(QuizSession.created_at.desc()).first()

        if participant_quiz_session:
            response_data["current_user_participant_quiz_session_id"] = participant_quiz_session.id
            print(f"Participant {current_user.id} found with specific quiz_session_id: {participant_quiz_session.id} for hosted_session {hosted_session_id}")
        else:
            print(f"Participant {current_user.id} record exists for hosted_session {hosted_session_id}, but no matching QuizSession found based on content.")
    return response_data

@router.post("/hosted/{hosted_session_id}/join", response_model=JoinHostedSessionResponse)
async def join_hosted_session(
    hosted_session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    hosted_session = db.query(HostedSession).filter(HostedSession.id == hosted_session_id).first()
    if not hosted_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hosted session not found")
    if not hosted_session.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is not active")
    if hosted_session.current_participants >= hosted_session.total_spots:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is full")

    # Find the template HostedQuizSession associated with the HostedSession
    template_hosted_quiz_session = db.query(HostedQuizSession).filter(HostedQuizSession.id == hosted_session.quiz_session_id).first()
    if not template_hosted_quiz_session:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Template quiz for hosted session not found")

    # Check if participant already exists for this user and hosted session
    participant_record = db.query(HostedSessionParticipant).filter(
        HostedSessionParticipant.hosted_session_id == hosted_session_id,
        HostedSessionParticipant.user_id == current_user.id
    ).first()

    participant_specific_quiz_session_id: Optional[UUID] = None

    if participant_record:
        # User has already joined. Try to find their existing QuizSession.
        # This assumes the QuizSession was created with matching details from template_hosted_quiz_session
        existing_quiz_session = db.query(QuizSession).filter(
            QuizSession.user_id == current_user.id,
            QuizSession.prompt == template_hosted_quiz_session.prompt,
            QuizSession.topic == template_hosted_quiz_session.topic,
            QuizSession.difficulty == template_hosted_quiz_session.difficulty,
            QuizSession.company == template_hosted_quiz_session.company,
            QuizSession.num_questions == template_hosted_quiz_session.num_questions
        ).order_by(QuizSession.created_at.desc()).first()
        if existing_quiz_session:
            participant_specific_quiz_session_id = existing_quiz_session.id
            print(f"User {current_user.id} already joined. Found their QuizSession: {participant_specific_quiz_session_id}")
        else:
            # This case is unlikely if join logic is correct, but handle it.
            # It means they are a participant but their QuizSession is missing or unmatchable.
            # We will proceed to create one below if not found.
            print(f"User {current_user.id} already joined but QuizSession not found by content match. Will attempt to create.")
            participant_record = None # Force creation path if their specific session is not found

    if not participant_record:
        if hosted_session.current_participants >= hosted_session.total_spots:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is full, cannot add new participant")
        
        participant_record = HostedSessionParticipant(
            id=uuid.uuid4(),
            hosted_session_id=hosted_session_id,
            user_id=current_user.id,
            joined_at=datetime.utcnow()
        )
        db.add(participant_record)
        hosted_session.current_participants += 1
        db.flush() # Flush to get participant_record.id if needed for leaderboard, and update counts
        print(f"New participant {current_user.id} added to hosted_session {hosted_session_id}")

    # Create or ensure QuizSession for the participant using template_hosted_quiz_session details
    # This part runs if participant_specific_quiz_session_id was not found above (either new join or missing session for existing participant)
    if not participant_specific_quiz_session_id:
        new_participant_quiz_session = QuizSession(
            id=uuid.uuid4(), # Generate new UUID for this participant's quiz session
            user_id=current_user.id,
            prompt=template_hosted_quiz_session.prompt,
            topic=template_hosted_quiz_session.topic,
            difficulty=template_hosted_quiz_session.difficulty,
            company=template_hosted_quiz_session.company,
            num_questions=template_hosted_quiz_session.num_questions,
            total_duration=template_hosted_quiz_session.total_duration,
            # started_at, submitted_at, score are default/None
        )
        db.add(new_participant_quiz_session)
        db.flush() # Ensure new_participant_quiz_session.id is available
        participant_specific_quiz_session_id = new_participant_quiz_session.id
        print(f"Created new QuizSession {participant_specific_quiz_session_id} for user {current_user.id} for hosted_session {hosted_session_id}")

        # Link questions from HostedQuizSessionQuestion to the new QuizSessionQuestion
        template_questions = db.query(HostedQuizSessionQuestion).filter(
            HostedQuizSessionQuestion.hosted_session_id == template_hosted_quiz_session.id
        ).order_by(HostedQuizSessionQuestion.question_order).all()

        for hq_question in template_questions:
            new_qs_question = QuizSessionQuestion(
                quiz_session_id=participant_specific_quiz_session_id,
                question_id=hq_question.question_id,
                question_order=hq_question.question_order
            )
            db.add(new_qs_question)
    
    db.commit()
    # db.refresh(hosted_session) # Refresh if needed for response, but we are constructing it manually
    # db.refresh(participant_record) # If its fields are directly used in response
    # If new_participant_quiz_session was created, db.refresh(new_participant_quiz_session)
    
    return JoinHostedSessionResponse(
        message="Successfully joined session" if not participant_record or not existing_quiz_session else "Already part of session, details retrieved",
        participant_quiz_session_id=participant_specific_quiz_session_id,
        hosted_session_id=hosted_session_id,
        is_live=bool(hosted_session.started_at) # Ensure is_live reflects current status
    )

@router.get("/{session_id}", response_model=QuizSessionResponse)
async def get_quiz_session(session_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(QuizSession).filter(
        QuizSession.id == session_id,
        QuizSession.user_id == current_user.id
    ).first()
    
    if not session:
        # This is a critical check. If a user is trying to access a QuizSession directly by its ID,
        # they MUST be the owner. Being a participant in a hosted session that *used* to link to this
        # QuizSession ID (if it was a template) does not grant direct access here.
        # The /hosted/{hosted_session_id} endpoint handles participant context for hosted sessions.
        raise HTTPException(status_code=404, detail="Quiz session not found or you are not the owner")
    return session

@router.get("/{session_id}/details")
async def get_session_details(session_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Based on usage in frontend (JoinSession.tsx calls getSessionDetails(sessionId) where sessionId is hosted_session_id)
    # this endpoint is fetching details for a HostedSession.
    hosted_session = db.query(HostedSession).filter(HostedSession.id == session_id).first()
    if not hosted_session:
        raise HTTPException(status_code=404, detail="Hosted session not found")

    host = db.query(User).filter(User.id == hosted_session.host_id).first()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found for the session")

    participants_query = (
        db.query(HostedSessionParticipant, User)
        .join(User, HostedSessionParticipant.user_id == User.id)
        .filter(HostedSessionParticipant.hosted_session_id == hosted_session.id)
        .all()
    )

    participant_list = []
    for participant_join_record, user_record in participants_query:
        leaderboard_entry = db.query(HostedSessionLeaderboard).filter(
            HostedSessionLeaderboard.participant_id == participant_join_record.id,
            HostedSessionLeaderboard.hosted_session_id == hosted_session.id
        ).first()

        participant_list.append({
            "id": str(user_record.id),
            "name": user_record.name,
            "score": leaderboard_entry.score if leaderboard_entry else 0,
            "position": leaderboard_entry.position if leaderboard_entry else 0,
            "started_at": leaderboard_entry.started_at.isoformat() if leaderboard_entry and leaderboard_entry.started_at else None,
            "submitted_at": leaderboard_entry.submitted_at.isoformat() if leaderboard_entry and leaderboard_entry.submitted_at else None,
            "avatar": user_record.avatar_url if hasattr(user_record, 'avatar_url') and user_record.avatar_url else f"https://ui-avatars.com/api/?name={user_record.name.replace(' ', '+')}"
        })

    return {
        "id": str(hosted_session.id),
        "title": hosted_session.title,
        "host": {
            "id": str(host.id),
            "name": host.name
        },
        "total_spots": hosted_session.total_spots,
        "current_participants": hosted_session.current_participants,
        "is_active": hosted_session.is_active,
        "participants": participant_list,
        "started_at": hosted_session.started_at.isoformat() if hosted_session.started_at else None,
        "ended_at": hosted_session.ended_at.isoformat() if hosted_session.ended_at else None,
    }

@router.post("/{session_id}/start", response_model=QuizSessionResponse, status_code=status.HTTP_200_OK)
async def start_quiz_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(QuizSession).filter(QuizSession.id == session_id, QuizSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Quiz session not found or not owned by user")
    if session.submitted_at:
        raise HTTPException(status_code=400, detail="Session already submitted")
    if session.started_at:
        # Optionally, allow re-starting if not submitted, or raise error/return current state
        # For now, let's assume starting an already started session is fine if not submitted.
        # db.refresh(session) # Refresh to ensure latest state, though not strictly necessary if no changes before commit
        # return session # Or just proceed to update leaderboard if logic requires
        pass

    session.started_at = datetime.utcnow()

    # If this QuizSession is part of any HostedSession (as a participant's session),
    # update the leaderboard entry.
    # This requires a way to link QuizSession back to HostedSessionParticipant or HostedSession.
    # Current model: HostedSession -> HostedQuizSession (template) -> QuizSession (participant's copy)
    # We need to find if this QuizSession (session_id) was created for a participant of a HostedSession.
    # This is complex without a direct link like `QuizSession.source_hosted_session_id`
    # or `QuizSession.participant_record_id`.

    # Let's assume for now the leaderboard entry is primarily managed when the HOST starts the HostedQuizSession,
    # or if the frontend explicitly passes hosted_session_id when a participant starts.
    # The current /start endpoint seems more for individual QuizSessions or host-initiated starts.

    # If we want to update participant's leaderboard on THEIR QuizSession start:
    # We'd need to find the HostedSessionParticipant record for this user and this QuizSession's content origin.
    # Example (conceptual, needs proper linking in DB schema):
    # participant_entry = db.query(HostedSessionParticipant).join(HostedSession).join(HostedQuizSession, HostedSession.quiz_session_id == HostedQuizSession.id)
    #    .filter(HostedSessionParticipant.user_id == current_user.id)
    #    .filter(HostedQuizSession.prompt == session.prompt) # matching content
    #    .filter(HostedQuizSession.topic == session.topic)   # matching content
    #    .first()
    # if participant_entry:
    #     leaderboard_entry = db.query(HostedSessionLeaderboard).filter(...).first()
    #     if not leaderboard_entry: create new one with started_at
    #     else: update started_at

    db.commit()
    db.refresh(session)
    return session

@router.get("/hosted/{hosted_session_id}/is-live")
async def is_hosted_session_live(hosted_session_id: UUID, db: Session = Depends(get_db)):
    hosted_session = db.query(HostedSession).filter(HostedSession.id == hosted_session_id).first()
    if not hosted_session or not hosted_session.started_at:
        return {"already_started": False}
    return {"already_started": True}

@router.post("/hosted-quiz-sessions/{hosted_quiz_session_id}/start", status_code=status.HTTP_200_OK)
async def start_hosted_quiz_session(
    hosted_quiz_session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    hosted_quiz_session = db.query(HostedQuizSession).filter(
        HostedQuizSession.id == hosted_quiz_session_id,
        HostedQuizSession.host_id == current_user.id
    ).first()
    if not hosted_quiz_session:
        raise HTTPException(status_code=404, detail="Hosted quiz session not found or you are not the host")
    if hosted_quiz_session.started_at:
        raise HTTPException(status_code=400, detail="Hosted quiz session already started")
    
    hosted_quiz_session.started_at = datetime.utcnow()
    db.flush() # Ensure started_at is set before updating related HostedSession

    # Also update the related HostedSession (the parent "room") if it exists and is not yet started
    # This links the start of the template quiz to the start of the actual hosted event.
    parent_hosted_session = db.query(HostedSession).filter(HostedSession.quiz_session_id == hosted_quiz_session_id).first()
    if parent_hosted_session and not parent_hosted_session.started_at:
        parent_hosted_session.started_at = hosted_quiz_session.started_at
        print(f"Updated parent HostedSession {parent_hosted_session.id} started_at to match HostedQuizSession {hosted_quiz_session_id}")
    
    db.commit()
    db.refresh(hosted_quiz_session)
    if parent_hosted_session: # Refresh if it was updated
        db.refresh(parent_hosted_session)
        
    return {"detail": "Hosted quiz session started successfully", "started_at": hosted_quiz_session.started_at}
