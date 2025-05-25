from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import User
from app.db.session import get_db
from app.core.security import get_password_hash, verify_password
from app.api.deps import get_current_user
from app.schemas.user import (
    UserCreate, UserResponse,
    UserUpdate, PasswordChangeRequest,UsernameAvailability, EmailVerificationRequest,EmailSchema
)
import uuid
import os
from datetime import datetime, timedelta
import random, string
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from app.core.config import settings

router = APIRouter(prefix="/users", tags=["Users"])

otp_store={}

def generate_otp(length: int = 6) -> str:
    """Generates a random OTP."""
    return "".join(random.choices(string.digits, k=length))

def verify_email(email: str, otp: str) -> bool:
    """Send OTP via email with QuickPrep logo"""
    try:
        # Create the email message container
        msg = MIMEMultipart()
        msg['From'] = settings.EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = "Your QuickPrep OTP for Secure Sign-In"

        

        # HTML body with the QuickPrep logo embedded
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="https://ibb.co/kVQns0rP" alt="QuickPrep Logo" style="width: 150px;"/>
            </div>
            <h2 style="color: #007bff; text-align: center;">Welcome to QuickPrep!</h2>
            <p style="text-align: center;">Use the OTP below to securely log in to your account:</p>
            <h1 style="font-size: 28px; text-align: center; color: #333;">{otp}</h1>
            <p style="text-align: center;">This OTP is valid for <strong>5 minutes</strong>.</p>
            <p style="text-align: center; color: #888;">If you didn’t request this OTP, you can safely ignore this email.</p>
            <br>
            <p style="text-align: center;">Thanks,<br><strong>The QuickPrep Team</strong></p>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        

        # Send email using SMTP
        server = smtplib.SMTP(settings.EMAIL_SERVER, settings.EMAIL_PORT)
        server.starttls()
        server.login(settings.EMAIL_ADDRESS, settings.EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        return True
    except Exception as e:
        print(f"Error sending QuickPrep OTP email: {e}")
        return False

@router.post("/send-otp")
async def send_verification_email(payload: EmailSchema,db: Session = Depends(get_db)):
    email = payload.email
    

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    otp = generate_otp()
    if not verify_email(email, otp):
        raise HTTPException(status_code=500, detail="Failed to send OTP")
    otp_store[email] = {
        'otp': otp,
        'expires_at': datetime.utcnow() + timedelta(minutes=5)  # OTP valid for 5 minutes
    }

    return {"message": "OTP sent successfully"}

@router.post("/verify-otp")
async def verify_email_otp(
    payload: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    email = payload.email
    otp = payload.otp

    if email not in otp_store:
        raise HTTPException(status_code=400, detail="Email not found or OTP expired")

    stored_otp = otp_store[email]
    if datetime.utcnow() > stored_otp['expires_at']:
        del otp_store[email]
        raise HTTPException(status_code=400, detail="OTP expired")

    if stored_otp['otp'] != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    
    # user = db.query(User).filter(User.email == email).first()
    # if not user:
    #     raise HTTPException(status_code=404, detail="User not found")

    # user.is_verified = True
    # db.commit()

    
    # del otp_store[email]

    return {"message": "Email verified and user updated successfully"}
  

@router.get("/check-username", response_model=UsernameAvailability)
def check_username(username: str, db: Session = Depends(get_db)):
    exists = db.query(User).filter(func.lower(User.name) == username.lower().strip()).first()
    print("Checked:", username, "Found:", exists)
    if exists is None:
        return {"available": True}
    else:   
        return {"available": False}
    


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
        is_verified=True  

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
