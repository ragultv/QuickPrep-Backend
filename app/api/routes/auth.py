from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from backend.app.db.session import get_db
from backend.app.db.models import User
from backend.app.core.security import verify_password, create_access_token, create_refresh_token
from backend.app.schemas.token import Token
from backend.app.api.deps import get_current_user
from datetime import datetime
from pydantic import BaseModel

class RefreshTokenRequest(BaseModel):
    refresh_token: str
router = APIRouter(prefix="/auth", tags=["Authentication"])

ACCESS_TOKEN_EXPIRE_MINUTES = 90
REFRESH_TOKEN_EXPIRE_DAYS = 7

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):  
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    return {
        "access_token": create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires),
        "refresh_token": create_refresh_token(data={"sub": str(user.id)}, expires_delta=refresh_token_expires),
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
def refresh_token(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    from backend.app.core.security import decode_token

    payload = decode_token(token_data.refresh_token)
    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    return {
        "access_token": create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires),
        "refresh_token": create_refresh_token(data={"sub": str(user.id)}, expires_delta=refresh_token_expires),
        "token_type": "bearer"
    }

@router.get("/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "created_at": current_user.created_at
    }
