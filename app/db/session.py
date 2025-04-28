from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings  # ✅ import the settings object

# ✅ use settings.DATABASE_URL instead of os.getenv
engine = create_engine("postgresql://postgres.fzjcejvmahoemdftwtuo:Pinnacle%402025@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
