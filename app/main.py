from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import get_db
from app.db.models import Base
from app.db.session import engine

from app.api.routes import auth, users, questions, quiz_sessions, answers,user_stats,quiz_result,quiz_resume
from app.api.routes import api_router
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Create the DB tables (if not using Alembic yet)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Quiz Platform", version="1.0.0")



# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://jovial-fenglisu-9a4cc0.netlify.app"],  # 👈 your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ✅ Include all API routes
app.include_router(users)           # ← this adds /users/register
app.include_router(auth)
app.include_router(questions)
app.include_router(quiz_sessions)
app.include_router(answers)
app.include_router(user_stats.router)
app.include_router(quiz_result.router)
app.include_router(quiz_resume.router)
#app.include_router(save_prompt_response.router)
app.include_router(api_router)
@app.get("/")
def root():
    return {"message": "Welcome to the Quiz Platform API"}
