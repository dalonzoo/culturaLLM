from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import and_, UniqueConstraint
from typing import List, Optional
from sqlalchemy.sql import func
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
import re

from backend.services.database import get_db
from backend.models.schemas import (
    Validation, Answer, Question, User, LLMValidation,
    ValidationCreate, ValidationResponse, PendingValidationResponse, CulturalTheme,
    QuestionModel, Base
)
from backend.routers.auth import get_current_user
from backend.services.llm_service import llm_service

router = APIRouter()

def update_user_score(user_id: int, points: int, db: Session):
    """
    Aggiorna il punteggio dell'utente e assegna badge in base ai risultati.
    
    Args:
        user_id: ID dell'utente da aggiornare
        points: Punti da aggiungere al punteggio
        db: Sessione del database
    
    Sistema Badge:
    - Bronze Validator: 100 punti
    - Silver Validator: 500 punti
    - Gold Validator: 1000 punti
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.score += points
        
        # Sistema di badge basato sul punteggio
        badges = user.badges.split(",") if user.badges else []
        
        # Assegnazione badge in base alle soglie di punteggio
        if user.score >= 100 and "Bronze Validator" not in badges:
            badges.append("Bronze Validator")
        if user.score >= 500 and "Silver Validator" not in badges:
            badges.append("Silver Validator")
        if user.score >= 1000 and "Gold Validator" not in badges:
            badges.append("Gold Validator")
        
        user.badges = ",".join(filter(None, badges))
        db.commit()



@router.post("/", response_model=ValidationResponse)
async def create_validation(
    validation: ValidationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crea una nuova validazione per una risposta e aggiorna i punteggi.
    
    Args:
        validation: Dati della validazione da creare
        current_user: Utente che sta effettuando la validazione
        db: Sessione del database
    
    Returns:
        La validazione creata
    
    Raises:
        HTTPException: 
        - 404 se la risposta non esiste
        - 400 se l'utente ha già validato questa risposta
        - 400 se l'utente tenta di validare la propria risposta
    
    Sistema Punti:
    - Validatore: 10 punti per validazione corretta, 5 per incorretta
    - Autore risposta: doppio del punteggio assegnato se >= 7
    """
    # Verifica che la risposta esista
    answer = db.query(Answer).filter(Answer.id == validation.answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    
    # Controlla se l'utente ha già validato questa risposta
    existing_validation = db.query(Validation).filter(
        and_(
            Validation.answer_id == validation.answer_id,
            Validation.validator_id == current_user.id
        )
    ).first()
    if existing_validation:
        raise HTTPException(status_code=400, detail="You have already validated this answer")
    
    # Impedisce all'utente di validare le proprie risposte
    if answer.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot validate your own answer")
    
    # Crea la validazione nel database
    db_validation = Validation(
        answer_id=validation.answer_id,
        validator_id=current_user.id,
        score=validation.score,
        is_correct=validation.is_correct,
        feedback=validation.feedback
    )
    db.add(db_validation)
    db.commit()
    db.refresh(db_validation)
    
    # Assegna punti al validatore
    points = 10 if validation.is_correct else 5  # Più punti per validazioni corrette
    update_user_score(current_user.id, points, db)
    
    # Assegna punti all'autore della risposta se la valutazione è positiva
    # Soglia aggiornata: score >= 4 (scala 1-5)
    if answer.user_id and validation.is_correct and validation.score >= 4:
        update_user_score(answer.user_id, int(validation.score * 2), db)
    
    
    
    return ValidationResponse.from_orm(db_validation)

@router.get("/pending", response_model=List[PendingValidationResponse])
async def get_pending_validations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Recupera le risposte che necessitano di validazione.
    Esclude le risposte dell'utente corrente e quelle già validate.
    
    Args:
        current_user: Utente che richiede le validazioni
        db: Sessione del database
    
    Returns:
        Lista di risposte da validare, ciascuna con:
        - Risposta utente
        - Domanda associata con tema
        - Risposta AI corrispondente (se presente)
    
    Note:
        Limita il risultato a 10 risposte per volta
    """
    print(f"\n=== Richiesta validazioni pendenti per utente {current_user.username} ===")
    
    # Trova le risposte già validate dall'utente
    subquery = db.query(Validation.answer_id).filter(
        Validation.validator_id == current_user.id
    ).subquery()
    
    # Recupera le risposte da validare
    answers = db.query(Answer).filter(
        Answer.user_id != current_user.id,  # Esclude le proprie risposte
        ~Answer.id.in_(subquery)  # Esclude risposte già validate
    ).limit(10).all()
    
    print(f"Trovate {len(answers)} risposte da validare")
    
    # Costruisce il risultato completo per ogni risposta
    result = []
    for answer in answers:
        print(f"\nProcessando risposta ID: {answer.id}")
        print(f"Testo risposta: {answer.text}")
        
        # Recupera la domanda con il tema
        question = db.query(Question).filter(Question.id == answer.question_id).first()
        if not question:
            print(f"Domanda non trovata per ID: {answer.question_id}")
            continue
            
        print(f"Domanda trovata: {question.text}")
            
        # Recupera il tema culturale
        theme = db.query(CulturalTheme).filter(CulturalTheme.id == question.theme_id).first()
        if not theme:
            print(f"Tema non trovato per ID: {question.theme_id}")
            continue
            
        print(f"Tema trovato: {theme.name}")
            
        # Recupera la risposta AI corrispondente
        llm_answer = db.query(Answer).filter(
            Answer.question_id == answer.question_id,
            Answer.is_llm_answer == True
        ).first()
        
        if llm_answer:
            print(f"Risposta LLM trovata: {llm_answer.text}")
        else:
            print("Nessuna risposta LLM trovata")
        
        # Associa il tema alla domanda
        question.theme = theme
        
        # Aggiunge la risposta completa al risultato
        result.append(PendingValidationResponse(
            answer=answer,
            question=question,
            llm_answer=llm_answer
        ))
    
    print(f"\nTotale risposte da validare restituite: {len(result)}")
    return result

@router.get("/answer/{answer_id}", response_model=List[ValidationResponse])
async def get_validations_for_answer(answer_id: int, db: Session = Depends(get_db)):
    """
    Recupera tutte le validazioni per una specifica risposta.
    
    Args:
        answer_id: ID della risposta
        db: Sessione del database
    
    Returns:
        Lista di tutte le validazioni per la risposta specificata
    """
    validations = db.query(Validation).filter(Validation.answer_id == answer_id).all()
    return validations

@router.post("/llm-validate", response_model=List[ValidationResponse])
async def validate_with_llm(
    answer_id: int,
    db: Session = Depends(get_db)
):
    """
    Valuta sia la risposta umana che la risposta LLM corrispondente utilizzando il modello LLM.
    Le validazioni vengono salvate nella tabella llm_validations.
    
    Returns:
        Lista di due ValidationResponse: una per la risposta umana e una per la risposta LLM
    """
    # Recupera la risposta umana e la domanda
    human_answer = db.query(Answer).filter(Answer.id == answer_id).first()
    if not human_answer:
        raise HTTPException(status_code=404, detail="Risposta umana non trovata")
    
    question = db.query(Question).filter(Question.id == human_answer.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Domanda non trovata")
    
    # Recupera la risposta LLM corrispondente
    llm_answer = db.query(Answer).filter(
        Answer.question_id == human_answer.question_id,
        Answer.is_llm_answer == True
    ).first()
    
    if not llm_answer:
        raise HTTPException(status_code=404, detail="Risposta LLM non trovata")
    
    validations = []
    
    # Funzione helper per validare una singola risposta con il nuovo servizio
    def validate_single_answer(answer_to_validate, is_llm=False):
        validation_data = llm_service.validate_answer(
            question=question.text,
            answer=answer_to_validate.text,
            feedback=""  # Feedback vuoto come da specifica
        )

        if not validation_data or "score" not in validation_data:
            raise HTTPException(
                status_code=500,
                detail="Errore durante la validazione con il servizio esterno: risposta non valida."
            )

        score = validation_data["score"]
        feedback_text = validation_data.get("feedback", f"Valutazione automatica: punteggio {score}/10.")

        llm_validation = LLMValidation(
            answer_id=answer_to_validate.id,
            score=score,
            is_correct=score >= 6,  # Soglia di correttezza
            feedback=feedback_text
        )

        db.add(llm_validation)
        db.commit()
        db.refresh(llm_validation)
        
        return ValidationResponse(
            id=llm_validation.id,
            answer_id=llm_validation.answer_id,
            validator_id=None,  # Esplicitamente None per LLM
            score=llm_validation.score,
            is_correct=llm_validation.is_correct,
            feedback=llm_validation.feedback,
            created_at=llm_validation.created_at
        )

    # Valida la risposta umana
    human_validation = validate_single_answer(human_answer, is_llm=False)
    
    # Valida la risposta LLM
    llm_validation = validate_single_answer(llm_answer, is_llm=True)
    
    return [human_validation, llm_validation]



@router.post("/llm-validate-text", response_model=List[ValidationResponse])
async def validate_with_llm_text(
    answer_text: str = Body(..., embed=True),
    question_text: str = Body("Domanda di esempio", embed=True),
    theme: str = Body("Tema generico", embed=True),
):
    """
    Valida una risposta arbitraria (non presente nel DB) e una risposta LLM generata al volo.
    Restituisce una lista di 2 ValidationResponse (mock, senza DB).
    """
    # Funzione helper per validare un testo arbitrario
    def validate_single_answer_text(answer_text_to_validate: str, question_text: str, theme: str) -> Optional[ValidationResponse]:
        validation_data = llm_service.validate_answer(
            question=question_text,
            answer=answer_text_to_validate,
            feedback=""
        )

        if not validation_data or "score" not in validation_data:
            return None # Gestisce l'errore in modo silente

        score = validation_data["score"]
        feedback_text = f"Valutazione automatica: punteggio {score}/10."
        
        # Crea un oggetto mock di ValidationResponse perché non c'è interazione con il DB
        return ValidationResponse(
            id=0,  # ID fittizio
            answer_id=0,
            validator_id=None,
            score=score,
            is_correct=score >= 6,
            feedback=feedback_text,
            created_at=func.now() # Data corrente
        )

    # Validazione della risposta utente
    user_validation = validate_single_answer_text(answer_text, question_text, theme)
    
    # Generazione e validazione della risposta LLM
    llm_generated_answer = llm_service.generate_answer(question_text, theme)
    llm_validation = validate_single_answer_text(llm_generated_answer, question_text, theme)
    
    # Filtra i risultati per escludere eventuali validazioni fallite
    results = [res for res in [user_validation, llm_validation] if res is not None]

    if not results:
        raise HTTPException(
            status_code=500,
            detail="Impossibile ottenere la validazione da servizio esterno."
        )

    return results
