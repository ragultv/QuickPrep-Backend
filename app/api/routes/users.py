from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.models import User
from app.db.session import get_db
from app.core.security import get_password_hash, verify_password
from app.api.deps import get_current_user
from app.schemas.user import (
    UserCreate, UserResponse,
    UserUpdate, PasswordChangeRequest
)
import uuid

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.name == user_in.name).first():
        raise HTTPException(status_code=400, detail="Username already registered")

    new_user = User(
        id=uuid.uuid4(),
        name=user_in.name,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/update", response_model=UserResponse)
def update_profile(update: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if update.email and update.email != current_user.email:
        if db.query(User).filter(User.email == update.email).first():
            raise HTTPException(status_code=400, detail="Email already in use")

    if update.name:
        current_user.name = update.name
    if update.email:
        current_user.email = update.email

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/change-password")
def change_password(
    request: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not verify_password(request.old_password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Old password is incorrect")

    current_user.password_hash = get_password_hash(request.new_password)
    db.commit()
    return {"message": "Password updated successfully"}


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
