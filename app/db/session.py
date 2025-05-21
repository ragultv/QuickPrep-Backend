from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings  # ✅ import the settings object

# ✅ use settings.DATABASE_URL instead of os.getenv (Pinnacle@2004)
engine = create_engine("postgresql://postgres.esobonzucjpgqcrvliac:Pinnacle%402004@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres")

#postgresql://postgres.esobonzucjpgqcrvliac:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
