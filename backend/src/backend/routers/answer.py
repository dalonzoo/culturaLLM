from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import re
from pydantic import BaseModel

from backend.services.database import get_db
from backend.services.llm_service import llm_service
from backend.models.schemas import (
    Answer, Question, User,
    AnswerCreate, AnswerResponse
)
from backend.routers.auth import get_current_user

router = APIRouter()

def clean_text(text: str) -> str:
    """
    Pulisce il testo della risposta rimuovendo caratteri indesiderati.
    
    Args:
        text: Il testo da pulire
        
    Returns:
        Il testo pulito da spazi multipli e caratteri non validi
        
    Operazioni:
    - Rimuove spazi multipli consecutivi
    - Rimuove spazi iniziali e finali
    - Elimina caratteri di controllo mantenendo solo newline
    """
    # Rimuove spazi multipli
    text = re.sub(r'\s+', ' ', text)
    # Rimuove spazi all'inizio e alla fine
    text = text.strip()
    # Rimuove caratteri di controllo mantenendo solo newline validi
    text = ''.join(char for char in text if ord(char) >= 32 or char == '\n')
    return text

async def generate_llm_answer_background(question_id: int, db: Session):
    """
    Task in background per generare la risposta del modello AI.
    Viene eseguito in modo asincrono per non bloccare la risposta all'utente.
    
    Args:
        question_id: ID della domanda da rispondere
        db: Sessione del database
    """
    # Recupera la domanda dal database
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        return
    
    # Genera la risposta AI usando il contesto culturale se disponibile
    cultural_context = question.theme.name if question.theme else ""
    llm_answer_text = llm_service.generate_answer(question.text, cultural_context)
    
    # Salva la risposta AI pulita nel database
    llm_answer = Answer(
        text=clean_text(llm_answer_text),
        question_id=question_id,
        user_id=None,  # Nessun utente associato per risposte AI
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
    """
    Crea una nuova risposta utente e genera una risposta AI in background.
    
    Args:
        answer: Dati della risposta da creare
        background_tasks: Gestore dei task in background
        current_user: Utente autenticato (da middleware)
        db: Sessione del database
        
    Returns:
        La risposta creata
        
    Raises:
        HTTPException: Se la domanda non esiste o l'utente ha già risposto
    """
    # Verifica che la domanda esista
    question = db.query(Question).filter(Question.id == answer.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Controlla se l'utente ha già risposto a questa domanda
    existing_answer = db.query(Answer).filter(
        Answer.question_id == answer.question_id,
        Answer.user_id == current_user.id
    ).first()
    if existing_answer:
        raise HTTPException(status_code=400, detail="You have already answered this question")
    
    # Crea la risposta dell'utente con testo pulito
    db_answer = Answer(
        text=clean_text(answer.text),
        question_id=answer.question_id,
        user_id=current_user.id,
        is_llm_answer=False
    )
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)
    
    # Genera la risposta AI in background se non esiste già
    llm_answer_exists = db.query(Answer).filter(
        Answer.question_id == answer.question_id,
        Answer.is_llm_answer == True
    ).first()
    
    if not llm_answer_exists:
        background_tasks.add_task(generate_llm_answer_background, answer.question_id, db)
    
    return AnswerResponse.from_orm(db_answer)

@router.get("/question/{question_id}", response_model=List[AnswerResponse])
async def get_answers_for_question(question_id: int, db: Session = Depends(get_db)):
    """
    Recupera tutte le risposte per una specifica domanda.
    
    Args:
        question_id: ID della domanda
        db: Sessione del database
        
    Returns:
        Lista di tutte le risposte associate alla domanda
    """
    answers = db.query(Answer).filter(Answer.question_id == question_id).all()
    return answers

@router.get("/{answer_id}", response_model=AnswerResponse)
async def get_answer(answer_id: int, db: Session = Depends(get_db)):
    """
    Recupera una specifica risposta tramite il suo ID.
    
    Args:
        answer_id: ID della risposta da recuperare
        db: Sessione del database
        
    Returns:
        La risposta richiesta
        
    Raises:
        HTTPException: Se la risposta non viene trovata
    """
    answer = db.query(Answer).filter(Answer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    return answer

class AnswerValidationRequest(BaseModel):
    answer_text: str
    question_id: int

class AnswerValidationResponse(BaseModel):
    is_correct: bool
    feedback: str
    correct_answer: str = None

@router.post("/validate", response_model=AnswerValidationResponse)
async def validate_answer(
    validation: AnswerValidationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Valida una risposta usando l'AI confrontandola con la risposta AI salvata
    """
    # Recupera la domanda
    question = db.query(Question).filter(Question.id == validation.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Recupera la risposta AI
    llm_answer = db.query(Answer).filter(
        Answer.question_id == validation.question_id,
        Answer.is_llm_answer == True
    ).first()
    
    if not llm_answer:
        raise HTTPException(status_code=404, detail="AI answer not found for this question")
    
    # Usa il servizio LLM per validare la risposta
    validation_result = llm_service.validate_answer(
        question_text=question.text,
        user_answer=validation.answer_text,
        correct_answer=llm_answer.text,
        cultural_context=question.theme.name if question.theme else ""
    )
    
    return AnswerValidationResponse(
        is_correct=validation_result["is_correct"],
        feedback=validation_result["feedback"],
        correct_answer=llm_answer.text if not validation_result["is_correct"] else None
    )
