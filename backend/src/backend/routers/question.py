from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body
from sqlalchemy.orm import Session
from typing import List
import random

from backend.services.database import get_db
from backend.services.llm_service import llm_service
from backend.models.schemas import (
    Question, CulturalTheme, User,
    QuestionCreate, QuestionResponse, CulturalThemeResponse,
    Answer, TagResponse
)
from backend.routers.auth import get_current_user

router = APIRouter()

async def generate_llm_answer_background(question_id: int, db: Session):
    """Background task to generate LLM answer"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        return
    
    # Generate LLM answer
    cultural_context = question.theme.name if question.theme else ""
    llm_answer_text = llm_service.generate_answer(question.text, cultural_context)
    
    # Save LLM answer
    llm_answer = Answer(
        text=llm_answer_text,
        question_id=question_id,
        user_id=None,
        is_llm_answer=True
    )
    db.add(llm_answer)
    db.commit()

@router.get("/themes", response_model=List[CulturalThemeResponse])
async def get_themes(db: Session = Depends(get_db)):
    themes = db.query(CulturalTheme).all()
    return themes

@router.get("/random-theme", response_model=CulturalThemeResponse)
async def get_random_theme(db: Session = Depends(get_db)):
    themes = db.query(CulturalTheme).all()
    if not themes:
        raise HTTPException(status_code=404, detail="No themes available")
    
    random_theme = random.choice(themes)
    return random_theme

@router.post("/", response_model=QuestionResponse)
async def create_question(
    question: QuestionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify theme exists
    theme = db.query(CulturalTheme).filter(CulturalTheme.id == question.theme_id).first()
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")
    # Genera il tag
    tag = llm_service.generate_tag(question.text)
    db_question = Question(
        text=question.text,
        creator_id=current_user.id,
        theme_id=question.theme_id,
        tag=tag
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    # Generate LLM answer in background
    background_tasks.add_task(generate_llm_answer_background, db_question.id, db)
    return QuestionResponse.from_orm(db_question)

@router.get("/", response_model=List[QuestionResponse])
async def get_questions(
    skip: int = 0,
    limit: int = 10,
    theme_id: int = None,
    db: Session = Depends(get_db)
):
    query = db.query(Question).filter(Question.is_active == True)
    
    if theme_id:
        query = query.filter(Question.theme_id == theme_id)
    
    questions = query.offset(skip).limit(limit).all()
    return questions

@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: int, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.get("/pending/answer")
async def get_pending_questions_for_answer(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get questions that need answers (excluding user's own questions and already answered)"""
    # Get questions that user has already answered
    answered_questions = db.query(Answer.question_id).filter(
        Answer.user_id == current_user.id
    ).subquery()
    
    # Get questions that need answers
    questions = db.query(Question).filter(
        Question.creator_id != current_user.id,  # Not user's own questions
        Question.is_active == True,  # Only active questions
        ~Question.id.in_(answered_questions)  # Not already answered by user
    ).limit(10).all()
    
    return questions

@router.post("/generate/{theme_id}")
async def generate_llm_question(
    theme_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Genera una nuova domanda sulla cultura italiana basata su un tema specifico.
    Restituisce solo il testo e il tag, NON salva nulla nel database.
    """
    # Verifica che il tema esista
    theme = db.query(CulturalTheme).filter(CulturalTheme.id == theme_id).first()
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")
    # Genera la domanda usando il servizio LLM
    prompt = f"""
    Genera una domanda semplice e veloce sulla cultura italiana riguardante il tema: {theme.name}
    La domanda deve essere:
    - Chiara e concisa
    - Specifica per il tema {theme.name}
    - Adatta a un quiz sulla cultura italiana
    - Non troppo lunga
    Formato richiesto: solo la domanda, senza spiegazioni aggiuntive.
    """
    try:
        question_text = llm_service.generate_answer(prompt)
        tag = llm_service.generate_tag(question_text.strip())
        return {"text": question_text.strip(), "tag": tag}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating question: {str(e)}"
        )

@router.post("/tag", response_model=TagResponse)
async def generate_tag_for_question(
    question: str = Body(..., embed=True)
):
    """
    Genera un tag riassuntivo (max 3 parole) per una domanda fornita.
    """
    tag = llm_service.generate_tag(question)
    return TagResponse(tag=tag)
