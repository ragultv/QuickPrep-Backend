import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
else:
    print(f"Warning: .env file not found at {env_path}")

class Settings:
    PROJECT_NAME: str = "Quiz Platform"
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = ENV == "development"
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "your-default-or-dev-key")
    BULK_GOOGLE_API_KEY: str = os.getenv("BULK_GOOGLE_API_KEY", "your-default-or-dev-key")
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "supersecretkey")
    SECRET_KEY: str = os.getenv("SECRET_KEY")  # Removed trailing comma
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    JWT_ALGORITHM: str = "HS256"
    OPENROUTER_API_KEY:str = os.getenv("OPEN_ROUTER_KEY")
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL")  
    # Remove duplicate ACCESS_TOKEN_EXPIRE_MINUTES if needed
    EMAIL_SERVER: str = os.getenv("EMAIL_SERVER", "smtp.example.com")
    EMAIL_PORT: int = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_ADDRESS: str = os.getenv("EMAIL_ADDRESS")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD")

settings = Settings()

# Optional debug log
#print(f"DEBUG >> DATABASE_URL: {settings.DATABASE_URL}")
#print(f"DEBUG >> SECRET_KEY: {settings.SECRET_KEY}")
