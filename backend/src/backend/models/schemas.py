from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

Base = declarative_base()

# SQLAlchemy Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    score = Column(Integer, default=0)
    badges = Column(Text, default="")  # JSON string of badges
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    questions = relationship("Question", back_populates="creator")
    answers = relationship("Answer", back_populates="user")
    validations = relationship("Validation", back_populates="validator")

class CulturalTheme(Base):
    __tablename__ = "cultural_themes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    questions = relationship("Question", back_populates="theme")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    theme_id = Column(Integer, ForeignKey("cultural_themes.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    tag = Column(String(100), nullable=True)
    
    creator = relationship("User", back_populates="questions")
    theme = relationship("CulturalTheme", back_populates="questions")
    answers = relationship("Answer", back_populates="question")

class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL for LLM answers
    is_llm_answer = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    question = relationship("Question", back_populates="answers")
    user = relationship("User", back_populates="answers")
    validations = relationship("Validation", back_populates="answer")
    llm_validations = relationship("LLMValidation", back_populates="answer")

class Validation(Base):
    __tablename__ = "validations"
    
    id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(Integer, ForeignKey("answers.id"), nullable=False)
    validator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Float, nullable=False)  # 0-10 score
    is_correct = Column(Boolean, nullable=False)
    feedback = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    answer = relationship("Answer", back_populates="validations")
    validator = relationship("User", back_populates="validations")

class LLMValidation(Base):
    __tablename__ = "llm_validations"
    
    id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(Integer, ForeignKey("answers.id"), nullable=False)
    score = Column(Float, nullable=False)  # 0-10 score
    is_correct = Column(Boolean, nullable=False)
    feedback = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    answer = relationship("Answer", back_populates="llm_validations")

class ValidatedTag(Base):
    __tablename__ = "validated_tags"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    tag = Column(String(100), nullable=False)
    score = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint('user_id', 'question_id', name='_user_question_uc'),)

# Pydantic Models
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    score: int
    badges: str
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class CulturalThemeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    
    class Config:
        from_attributes = True

class QuestionCreate(BaseModel):
    text: str
    theme_id: int

class QuestionResponse(BaseModel):
    id: int
    text: str
    creator_id: int
    theme_id: int
    created_at: datetime
    theme: CulturalThemeResponse
    tag: Optional[str] = None
    
    class Config:
        from_attributes = True

class AnswerCreate(BaseModel):
    text: str
    question_id: int

class AnswerResponse(BaseModel):
    id: int
    text: str
    question_id: int
    user_id: Optional[int]
    is_llm_answer: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ValidationCreate(BaseModel):
    answer_id: int
    score: float
    is_correct: bool
    feedback: Optional[str]

class ValidationResponse(BaseModel):
    id: int
    answer_id: int
    validator_id: Optional[int]
    score: float
    is_correct: bool
    feedback: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class PendingValidationResponse(BaseModel):
    answer: AnswerResponse
    question: QuestionResponse
    llm_answer: Optional[AnswerResponse]
    
    class Config:
        from_attributes = True

class LeaderboardEntry(BaseModel):
    username: str
    score: int
    badges: str
    rank: int

class QuestionModel(BaseModel):
    id: int
    text: str
    creator_id: int
    theme_id: int
    created_at: datetime
    is_active: bool
    theme: Optional[CulturalThemeResponse] = None
    tag: Optional[str] = None

    class Config:
        from_attributes = True

class TagResponse(BaseModel):
    tag: str

class ValidatedTagResponse(BaseModel):
    tag: str
    score: float
    question_id: int
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class ValidatedTagResponseList(BaseModel):
    items: list[ValidatedTagResponse]
