from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List

from backend.services.database import get_db
from backend.models.schemas import (
    Validation, Answer, Question, User,
    ValidationCreate, ValidationResponse, PendingValidationResponse, CulturalTheme,
    QuestionModel
)
from backend.routers.auth import get_current_user

router = APIRouter()

def update_user_score(user_id: int, points: int, db: Session):
    """Update user score and check for badges"""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.score += points
        
        # Simple badge system
        badges = user.badges.split(",") if user.badges else []
        
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
    # Verify answer exists
    answer = db.query(Answer).filter(Answer.id == validation.answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    
    # Check if user already validated this answer
    existing_validation = db.query(Validation).filter(
        and_(
            Validation.answer_id == validation.answer_id,
            Validation.validator_id == current_user.id
        )
    ).first()
    if existing_validation:
        raise HTTPException(status_code=400, detail="You have already validated this answer")
    
    # Check if user is trying to validate their own answer
    if answer.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot validate your own answer")
    
    # Create validation
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
    
    # Update validator score
    points = 10 if validation.is_correct else 5  # More points for correct validations
    update_user_score(current_user.id, points, db)
    
    # Update answer author score if validation is positive
    if answer.user_id and validation.is_correct and validation.score >= 7:
        update_user_score(answer.user_id, int(validation.score * 2), db)
    
    return ValidationResponse.from_orm(db_validation)

@router.get("/pending", response_model=List[PendingValidationResponse])
async def get_pending_validations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get answers that need validation (excluding user's own answers)"""
    print(f"\n=== Richiesta validazioni pendenti per utente {current_user.username} ===")
    
    # Get answers that haven't been validated by current user
    subquery = db.query(Validation.answer_id).filter(
        Validation.validator_id == current_user.id
    ).subquery()
    
    # Get answers with their questions and LLM answers
    answers = db.query(Answer).filter(
        Answer.user_id != current_user.id,  # Not user's own answers
        ~Answer.id.in_(subquery)  # Not already validated by user
    ).limit(10).all()
    
    print(f"Trovate {len(answers)} risposte da validare")
    
    # For each answer, get the corresponding question and LLM answer
    result = []
    for answer in answers:
        print(f"\nProcessando risposta ID: {answer.id}")
        print(f"Testo risposta: {answer.text}")
        
        # Get question with theme
        question = db.query(Question).filter(Question.id == answer.question_id).first()
        if not question:
            print(f"Domanda non trovata per ID: {answer.question_id}")
            continue
            
        print(f"Domanda trovata: {question.text}")
            
        # Get theme
        theme = db.query(CulturalTheme).filter(CulturalTheme.id == question.theme_id).first()
        if not theme:
            print(f"Tema non trovato per ID: {question.theme_id}")
            continue
            
        print(f"Tema trovato: {theme.name}")
            
        # Get LLM answer
        llm_answer = db.query(Answer).filter(
            Answer.question_id == answer.question_id,
            Answer.is_llm_answer == True
        ).first()
        
        if llm_answer:
            print(f"Risposta LLM trovata: {llm_answer.text}")
        else:
            print("Nessuna risposta LLM trovata")
        
        # Add theme to question
        question.theme = theme
        
        result.append(PendingValidationResponse(
            answer=answer,
            question=question,
            llm_answer=llm_answer
        ))
    
    print(f"\nTotale risposte da validare restituite: {len(result)}")
    return result

@router.get("/answer/{answer_id}", response_model=List[ValidationResponse])
async def get_validations_for_answer(answer_id: int, db: Session = Depends(get_db)):
    validations = db.query(Validation).filter(Validation.answer_id == answer_id).all()
    return validations
