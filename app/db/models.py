from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float,JSON
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import CHAR, Text


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    quiz_sessions = relationship("QuizSession", back_populates="user")


class Question(Base):
    __tablename__ = "questions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hash = Column(Text, unique=True, nullable=False)
    question_text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_answer = Column(CHAR(1), nullable=False)
    explanation = Column(Text, nullable=False)
    topic = Column(String(100))
    difficulty = Column(String(100))
    company = Column(String(100))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    created_user = relationship("User", backref="questions")


class QuizSession(Base):
    __tablename__ = "quiz_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    prompt = Column(Text, nullable=False)
    topic = Column(String(100))
    difficulty = Column(String(100))
    company = Column(String(100))
    num_questions = Column(Integer, default=0)
    score = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime)
    user = relationship("User", back_populates="quiz_sessions")
    questions = relationship("QuizSessionQuestion", back_populates="quiz_session")
    answers = relationship("UserAnswer", back_populates="quiz_session")
    total_duration = Column(Float, nullable=False)


class QuizSessionQuestion(Base):
    __tablename__ = "quiz_session_questions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_session_id = Column(UUID(as_uuid=True), ForeignKey("quiz_sessions.id"))
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"))
    question_order = Column(Integer)
    quiz_session = relationship("QuizSession", back_populates="questions")
    question = relationship("Question")


class UserAnswer(Base):
    __tablename__ = "user_answers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_session_id = Column(UUID(as_uuid=True), ForeignKey("quiz_sessions.id"))
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"))
    selected_option = Column(CHAR(1), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    answered_at = Column(DateTime, default=datetime.utcnow)

    quiz_session = relationship("QuizSession", back_populates="answers")
    question = relationship("Question")

class resume(Base):
    __tablename__ = "resumes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_url = Column(Text, nullable=False)
    content = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="resumes")

class PromptResponse(Base):
    __tablename__ = "prompt_responses"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True) 
    prompt = Column(String, index=True)
    response = Column(JSON)