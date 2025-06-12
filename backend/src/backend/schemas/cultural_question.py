from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class QuestionCreate(BaseModel):
    topic: str = Field(..., description="L'argomento della domanda culturale")

class QuestionResponse(BaseModel):
    id: int
    topic: str
    question: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class AnswerCreate(BaseModel):
    question_id: int
    answer_text: str = Field(..., description="La risposta fornita alla domanda")

class AnswerEvaluation(BaseModel):
    score: float = Field(..., ge=1, le=5, description="Voto da 1 a 5")
    evaluation: str = Field(..., description="Spiegazione della valutazione")
    
    class Config:
        from_attributes = True

class AnswerResponse(BaseModel):
    id: int
    question_id: int
    answer_text: str
    score: float
    evaluation: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class QuestionWithAnswers(QuestionResponse):
    answers: List[AnswerResponse] = []
    
    class Config:
        from_attributes = True 