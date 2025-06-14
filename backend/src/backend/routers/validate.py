from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, UniqueConstraint
from typing import List
from sqlalchemy.sql import func
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
import re

from backend.services.database import get_db
from backend.models.schemas import (
    Validation, Answer, Question, User, LLMValidation,
    ValidationCreate, ValidationResponse, PendingValidationResponse, CulturalTheme,
    QuestionModel, ValidatedTag, ValidatedTagResponse, ValidatedTagResponseList, Base
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

def save_validated_tag(user_id: int, question_id: int, tag: str, score: float, db: Session):
    # Non salvare se il tag è None o vuoto
    if not tag:
        print(f"[WARN] Tag mancante per question_id={question_id}, user_id={user_id}. Non salvo validated_tag.")
        return
    # Cerca duplicati anche per tag e score
    existing = db.query(ValidatedTag).filter_by(user_id=user_id, question_id=question_id, tag=tag, score=score).first()
    if existing:
        return  # Non salvare duplicati esatti
    db.add(ValidatedTag(user_id=user_id, question_id=question_id, tag=tag, score=score))
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
    if answer.user_id and validation.is_correct and validation.score >= 7:
        update_user_score(answer.user_id, int(validation.score * 2), db)
    
    question = db.query(Question).filter(Question.id == answer.question_id).first()
    if question and question.tag:
        # Salva per il validatore
        save_validated_tag(current_user.id, question.id, question.tag, validation.score, db)
        # Salva per il rispondente solo se diverso dal validatore e diverso dal creatore della domanda
        if answer.user_id and answer.user_id != current_user.id and answer.user_id != question.creator_id:
            save_validated_tag(answer.user_id, question.id, question.tag, validation.score, db)
    
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

@router.post("/llm-validate", response_model=ValidationResponse)
async def validate_with_llm(
    answer_id: int,
    db: Session = Depends(get_db)
):
    """
    Valida una risposta utilizzando il modello LLM.
    La validazione viene salvata nella tabella llm_validations.
    """
    # Recupera la risposta e la domanda
    answer = db.query(Answer).filter(Answer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Risposta non trovata")
    
    question = db.query(Question).filter(Question.id == answer.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Domanda non trovata")
    
    # Costruisci il prompt per la validazione
    prompt = f"""
    Valuta la seguente risposta a una domanda sulla cultura italiana.
    
    Domanda: {question.text}
    Tema: {question.theme.name if question.theme else 'N/A'}
    Risposta da valutare: {answer.text}
    
    Valuta la risposta considerando:
    1. Correttezza (accuratezza delle informazioni)
    2. Rilevanza (pertinenza rispetto alla domanda)
    3. Dettaglio (completezza della risposta)
    4. Chiarezza (comprensibilità e struttura)
    
    Fornisci:
    1. Un punteggio da 1 a 5 per ogni criterio
    2. Un punteggio complessivo da 1 a 5
    3. Un breve feedback che spieghi la valutazione
    
    Formato richiesto:
    Correttezza: [1-5]
    Rilevanza: [1-5]
    Dettaglio: [1-5]
    Chiarezza: [1-5]
    Punteggio complessivo: [1-5]
    Feedback: [breve spiegazione]
    """
    
    # Ottieni la valutazione dal LLM
    llm_response = llm_service.generate_answer(prompt)
    
    # Estrai il punteggio complessivo e il feedback
    try:
        # Cerca il punteggio complessivo
        score_line = [line for line in llm_response.split('\n') if 'Punteggio complessivo:' in line][0]
        score_str = score_line.split(':')[1].strip()
        match = re.search(r'([1-5])', score_str)
        if not match:
            raise ValueError(f"Punteggio non trovato nel testo: {score_str}")
        score = float(match.group(1))
        
        # Cerca il feedback
        feedback_line = [line for line in llm_response.split('\n') if 'Feedback:' in line][0]
        feedback = feedback_line.split(':')[1].strip()
        
        # Normalizza il punteggio su una scala da 0 a 10
        normalized_score = (score / 5) * 10
        
        # Crea la validazione LLM
        llm_validation = LLMValidation(
            answer_id=answer_id,
            score=normalized_score,
            is_correct=normalized_score >= 6,
            feedback=feedback
        )
        
        db.add(llm_validation)
        db.commit()
        db.refresh(llm_validation)
        
        return ValidationResponse(
            id=llm_validation.id,
            answer_id=llm_validation.answer_id,
            validator_id=None,  # Nessun validatore umano
            score=llm_validation.score,
            is_correct=llm_validation.is_correct,
            feedback=llm_validation.feedback,
            created_at=llm_validation.created_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore nell'elaborazione della risposta LLM: {str(e)}")

@router.get("/validated-tags/me", response_model=ValidatedTagResponseList)
async def get_my_validated_tags(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Restituisce tutti i tag e punteggi delle domande validate dall'utente (come validatore).
    """
    # Prendi solo le validazioni dove l'utente è stato validatore
    validated_questions = db.query(Validation.answer_id).filter(Validation.validator_id == current_user.id).subquery()
    # Trova le domande associate a queste risposte
    validated_question_ids = db.query(Answer.question_id).filter(Answer.id.in_(validated_questions)).distinct()
    tags = db.query(ValidatedTag).filter(ValidatedTag.user_id == current_user.id, ValidatedTag.question_id.in_(validated_question_ids)).all()
    return ValidatedTagResponseList(items=tags)

@router.get("/validated-tags/by-answers", response_model=ValidatedTagResponseList)
async def get_validated_tags_by_answers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Restituisce tutti i tag e punteggi delle domande a cui l'utente ha risposto (solo i suoi).
    """
    # Trova tutte le domande a cui l'utente ha risposto
    answered_questions = db.query(Answer.question_id).filter(Answer.user_id == current_user.id).distinct()
    tags = db.query(ValidatedTag).filter(
        ValidatedTag.user_id == current_user.id,
        ValidatedTag.question_id.in_(answered_questions)
    ).all()
    return ValidatedTagResponseList(items=tags)
