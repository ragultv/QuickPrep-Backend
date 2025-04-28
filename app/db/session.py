from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.config import settings  # ✅ import the settings object

# ✅ use settings.DATABASE_URL instead of os.getenv
engine = create_engine("postgresql://postgres:ragul%402004@localhost:5432/Quizforge")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
