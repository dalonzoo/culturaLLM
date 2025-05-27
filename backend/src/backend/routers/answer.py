from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import re

from backend.services.database import get_db
from backend.services.llm_service import llm_service
from backend.models.schemas import (
    Answer, Question, User,
    AnswerCreate, AnswerResponse
)
from backend.routers.auth import get_current_user

router = APIRouter()

def clean_text(text: str) -> str:
    """Pulisce il testo rimuovendo spazi extra e caratteri non necessari"""
    # Rimuove spazi multipli
    text = re.sub(r'\s+', ' ', text)
    # Rimuove spazi all'inizio e alla fine
    text = text.strip()
    # Rimuove caratteri di controllo
    text = ''.join(char for char in text if ord(char) >= 32 or char == '\n')
    return text

async def generate_llm_answer_background(question_id: int, db: Session):
    """Background task to generate LLM answer"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        return
    
    # Generate LLM answer
    cultural_context = question.theme.name if question.theme else ""
    llm_answer_text = llm_service.generate_answer(question.text, cultural_context)
    
    # Clean and save LLM answer
    llm_answer = Answer(
        text=clean_text(llm_answer_text),
        question_id=question_id,
        user_id=None,
        is_llm_answer=True
    )
    db.add(llm_answer)
    db.commit()

@router.post("/", response_model=AnswerResponse)
async def create_answer(
    answer: AnswerCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify question exists
    question = db.query(Question).filter(Question.id == answer.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Check if user already answered this question
    existing_answer = db.query(Answer).filter(
        Answer.question_id == answer.question_id,
        Answer.user_id == current_user.id
    ).first()
    if existing_answer:
        raise HTTPException(status_code=400, detail="You have already answered this question")
    
    # Create user answer with cleaned text
    db_answer = Answer(
        text=clean_text(answer.text),
        question_id=answer.question_id,
        user_id=current_user.id,
        is_llm_answer=False
    )
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)
    
    # Generate LLM answer in background if not exists
    llm_answer_exists = db.query(Answer).filter(
        Answer.question_id == answer.question_id,
        Answer.is_llm_answer == True
    ).first()
    
    if not llm_answer_exists:
        background_tasks.add_task(generate_llm_answer_background, answer.question_id, db)
    
    return AnswerResponse.from_orm(db_answer)

@router.get("/question/{question_id}", response_model=List[AnswerResponse])
async def get_answers_for_question(question_id: int, db: Session = Depends(get_db)):
    answers = db.query(Answer).filter(Answer.question_id == question_id).all()
    return answers

@router.get("/{answer_id}", response_model=AnswerResponse)
async def get_answer(answer_id: int, db: Session = Depends(get_db)):
    answer = db.query(Answer).filter(Answer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    return answer
