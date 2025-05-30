from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.models import QuizSession, QuizSessionQuestion, Question, UserAnswer, HostedSession, HostedSessionParticipant, HostedQuizSession, HostedQuizSessionQuestion, HostedSessionLeaderboard, JoinedQuizSession, JoinedUserAnswer
from app.db.session import get_db
from app.api.deps import get_current_user
from app.schemas.user_answer import AnswerSubmission, AnswerResponse
from datetime import datetime
import uuid
from datetime import timezone
from typing import List

router = APIRouter(prefix="/answers", tags=["Answers"])

@router.post("/submit", response_model=dict)
def submit_answers(
    submission: AnswerSubmission,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Try to get the session as the owner
    session = db.query(QuizSession).filter(
        QuizSession.id == submission.quiz_session_id,
        QuizSession.user_id == current_user.id
    ).first()

    if not session:
        # If not the owner, check if the user is a participant in a hosted session for this quiz session
        participant = (
            db.query(HostedSessionParticipant)
            .join(HostedSession, HostedSessionParticipant.hosted_session_id == HostedSession.id)
            .filter(
                HostedSession.quiz_session_id == submission.quiz_session_id,
                HostedSessionParticipant.user_id == current_user.id
            )
            .first()
        )
        if participant:
            session = db.query(QuizSession).filter(QuizSession.id == submission.quiz_session_id).first()

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

    # Update leaderboard if this is a hosted session
    hosted_session = db.query(HostedSession).filter(HostedSession.quiz_session_id == session.id).first()
    if hosted_session:
        participant = db.query(HostedSessionParticipant).filter(
            HostedSessionParticipant.hosted_session_id == hosted_session.id,
            HostedSessionParticipant.user_id == current_user.id
        ).first()

        if participant:
            # Get or create leaderboard entry
            leaderboard_entry = db.query(HostedSessionLeaderboard).filter(
                HostedSessionLeaderboard.participant_id == participant.id,
                HostedSessionLeaderboard.hosted_session_id == hosted_session.id
            ).first()

            if not leaderboard_entry:
                leaderboard_entry = HostedSessionLeaderboard(
                    participant_id=participant.id,
                    hosted_session_id=hosted_session.id,
                    score=score,
                    position=0,
                    started_at=session.started_at,
                    submitted_at=session.submitted_at
                )
                db.add(leaderboard_entry)
            else:
                leaderboard_entry.score = score
                leaderboard_entry.submitted_at = session.submitted_at

            # Update positions for all participants
            all_entries = db.query(HostedSessionLeaderboard).filter(
                HostedSessionLeaderboard.hosted_session_id == hosted_session.id
            ).order_by(HostedSessionLeaderboard.score.desc()).all()

            for idx, entry in enumerate(all_entries, 1):
                entry.position = idx

    # Update hosted session ended_at if all participants have submitted
    if hosted_session and not hosted_session.ended_at:
        participant_sessions = db.query(QuizSession).filter(QuizSession.id == hosted_session.quiz_session_id).all()
        if all(qs.submitted_at is not None for qs in participant_sessions):
            hosted_session.ended_at = session.submitted_at
            hosted_session.is_active = False

    db.commit()

    return {
        "message": "Answers submitted successfully",
        "score": score,
        "total_questions": len(submission.answers),
        "correct_answers": score,
        "incorrect_answers": len(submission.answers) - score,
        "results": results  # Include detailed results
    }

@router.post("/submit-hosted", response_model=dict)
def submit_hosted_answers(
    submission: AnswerSubmission,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Submit answers for a hosted session as a participant. Each participant has their own QuizSession or JoinedQuizSession linked to the hosted session.
    """
    # Try to get the participant's QuizSession
    participant_quiz_session = db.query(QuizSession).filter(
        QuizSession.id == submission.quiz_session_id,
        QuizSession.user_id == current_user.id
    ).first()

    is_joined_session = False
    if not participant_quiz_session:
        # Try to get the participant's JoinedQuizSession
        participant_quiz_session = db.query(JoinedQuizSession).filter(
            JoinedQuizSession.id == submission.quiz_session_id,
            JoinedQuizSession.user_id == current_user.id
        ).first()
        is_joined_session = True if participant_quiz_session else False

    if not participant_quiz_session:
        raise HTTPException(status_code=404, detail="Participant's quiz session not found or you are not the owner.")

    if participant_quiz_session.submitted_at:
        raise HTTPException(status_code=400, detail="Quiz already submitted by this participant")

    # Find the HostedSession and participant record for this user
    hosted_session = None
    participant_record = None
    if is_joined_session:
        # For JoinedQuizSession, find the HostedSession via the template quiz
        # Find all HostedSessionParticipant records for this user
        participant_entries = db.query(HostedSessionParticipant).filter(
            HostedSessionParticipant.user_id == current_user.id
        ).all()
        for p_entry in participant_entries:
            hs = db.query(HostedSession).filter(HostedSession.id == p_entry.hosted_session_id).first()
            if hs:
                template_quiz = db.query(HostedQuizSession).filter(HostedQuizSession.id == hs.quiz_session_id).first()
                if (template_quiz and
                    template_quiz.prompt == participant_quiz_session.prompt and
                    template_quiz.topic == participant_quiz_session.topic and
                    template_quiz.difficulty == participant_quiz_session.difficulty and
                    template_quiz.company == participant_quiz_session.company and
                    template_quiz.num_questions == participant_quiz_session.num_questions):
                    hosted_session = hs
                    participant_record = p_entry
                    break
    else:
        # For QuizSession, find HostedSession by matching quiz_session_id
        hosted_session = db.query(HostedSession).filter(
            HostedSession.quiz_session_id == participant_quiz_session.id
        ).first()
        if hosted_session:
            participant_record = db.query(HostedSessionParticipant).filter(
                HostedSessionParticipant.hosted_session_id == hosted_session.id,
                HostedSessionParticipant.user_id == current_user.id
            ).first()

    if not hosted_session or not participant_record:
        raise HTTPException(status_code=404, detail="Could not reliably associate this quiz submission with an active hosted session for this participant.")

    score = 0
    results = []

    for answer in submission.answers:
        question = db.query(Question).filter(Question.id == answer.question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail=f"Question not found: {answer.question_id}")

        correct_answer_str = chr(question.correct_answer) if isinstance(question.correct_answer, int) else question.correct_answer
        is_correct = (answer.selected_option.upper() == correct_answer_str.upper())
        if is_correct:
            score += 1

        if is_joined_session:
            db_answer = JoinedUserAnswer(
                id=uuid.uuid4(),
                joined_session_id=participant_quiz_session.id,
                question_id=answer.question_id,
                selected_option=answer.selected_option.upper(),
                is_correct=is_correct,
                answered_at=datetime.utcnow()
            )
        else:
            db_answer = UserAnswer(
                id=uuid.uuid4(),
                quiz_session_id=participant_quiz_session.id,
                question_id=answer.question_id,
                selected_option=answer.selected_option.upper(),
                is_correct=is_correct,
                answered_at=datetime.utcnow()
            )
        db.add(db_answer)

        results.append({
            "question_id": answer.question_id,
            "selected_option": answer.selected_option.upper(),
            "correct_answer": correct_answer_str.upper(),
            "is_correct": is_correct,
            "explanation": question.explanation
        })

    participant_quiz_session.score = score
    participant_quiz_session.submitted_at = datetime.now(timezone.utc)

    # Update leaderboard entry for this participant
    leaderboard_entry = db.query(HostedSessionLeaderboard).filter(
        HostedSessionLeaderboard.participant_id == participant_record.id, 
        HostedSessionLeaderboard.hosted_session_id == hosted_session.id
    ).first()

    if not leaderboard_entry:
        leaderboard_entry = HostedSessionLeaderboard(
            participant_id=participant_record.id,
            hosted_session_id=hosted_session.id,
            score=score,
            position=0, 
            started_at=participant_quiz_session.started_at, 
            submitted_at=participant_quiz_session.submitted_at
        )
        db.add(leaderboard_entry)
    else:
        leaderboard_entry.score = score
        leaderboard_entry.submitted_at = participant_quiz_session.submitted_at

    # Update positions for all participants
    all_entries = db.query(HostedSessionLeaderboard).filter(
        HostedSessionLeaderboard.hosted_session_id == hosted_session.id
    ).order_by(HostedSessionLeaderboard.score.desc(), HostedSessionLeaderboard.submitted_at.asc()).all()
    for idx, entry in enumerate(all_entries, 1):
        entry.position = idx

    # Check if all participants have submitted
    if all(entry.submitted_at is not None for entry in all_entries):
        hosted_session.ended_at = participant_quiz_session.submitted_at
        hosted_session.is_active = False

    db.commit()

    return {
        "message": "Answers submitted successfully for hosted session",
        "quiz_session_id": participant_quiz_session.id,
        "score": score,
        "total_questions": len(submission.answers),
        "results": results
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
