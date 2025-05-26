from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings  # ✅ import the settings object
from sqlalchemy.pool import QueuePool

# ✅ use settings.DATABASE_URL instead of os.getenv (Pinnacle@2004)
engine = create_engine("postgresql://postgres.esobonzucjpgqcrvliac:Pinnacle%402004@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres",
    poolclass=QueuePool,
    pool_size=20,  # Maximum number of connections to keep
    max_overflow=10,  # Maximum number of connections that can be created beyond pool_size
    pool_timeout=30,  # Seconds to wait before giving up on getting a connection from the pool
    pool_recycle=1800,  # Recycle connections after 30 minutes
    pool_pre_ping=True )

#postgresql://postgres.esobonzucjpgqcrvliac:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
