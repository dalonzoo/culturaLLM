from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..services.database import get_db
from ..services.cultural_question_service import CulturalQuestionService
from ..schemas.cultural_question import (
    QuestionCreate,
    QuestionResponse,
    AnswerCreate,
    AnswerResponse,
    AnswerEvaluation,
    QuestionWithAnswers
)

router = APIRouter(
    prefix="/api/cultural-questions",
    tags=["cultural-questions"]
)

@router.post("/generate", response_model=QuestionResponse)
def generate_question(
    question_create: QuestionCreate,
    db: Session = Depends(get_db)
):
    """
    Genera una nuova domanda culturale dato un argomento.
    """
    service = CulturalQuestionService(db)
    try:
        question = service.generate_question(question_create.topic)
        return question
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate-answer", response_model=AnswerResponse)
def evaluate_answer(
    answer_create: AnswerCreate,
    db: Session = Depends(get_db)
):
    """
    Valuta una risposta data a una domanda culturale.
    """
    service = CulturalQuestionService(db)
    try:
        answer = service.evaluate_answer(
            answer_create.question_id,
            answer_create.answer_text
        )
        return answer
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 