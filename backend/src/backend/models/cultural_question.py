from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from backend.services.database import Base

class CulturalQuestion(Base):
    __tablename__ = "cultural_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(255), nullable=False)
    question = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relazione one-to-many con le risposte
    answers = relationship("QuestionAnswer", back_populates="question")

class QuestionAnswer(Base):
    __tablename__ = "question_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("cultural_questions.id"))
    answer_text = Column(Text, nullable=False)
    score = Column(Float, nullable=False)  # Voto da 1 a 5
    evaluation = Column(Text, nullable=False)  # Spiegazione della valutazione
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relazione many-to-one con la domanda
    question = relationship("CulturalQuestion", back_populates="answers") 