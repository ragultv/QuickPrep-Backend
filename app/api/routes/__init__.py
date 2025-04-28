from fastapi import APIRouter

from .auth import router as auth
from .users import router as users
from .questions import router as questions
from .quiz_sessions import router as quiz_sessions
from .answers import router as answers

api_router = APIRouter()

api_router.include_router(questions, prefix="/questions", tags=["Questions"])
api_router.include_router(quiz_sessions, prefix="/quiz-sessions", tags=["Quiz Sessions"])
api_router.include_router(answers, prefix="/answers", tags=["Answers"])
api_router.include_router(auth, prefix="/auth", tags=["Auth"])
api_router.include_router(users, prefix="/users", tags=["Users"])
api_router.include_router(users, prefix="/user_stats", tags=["User Stats"])
