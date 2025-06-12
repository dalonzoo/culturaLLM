from sqlalchemy.orm import Session
import requests
from typing import Optional
import os       # Per accedere alle variabili d'ambiente
from ..models.cultural_question import CulturalQuestion, QuestionAnswer
from ..schemas.cultural_question import QuestionCreate, AnswerCreate

# Se non specificate, usa i valori di default per lo sviluppo locale
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2:2b")
class CulturalQuestionService:
    def __init__(self, db: Session):
        self.db = db
        self.host = OLLAMA_HOST
        self.model = OLLAMA_MODEL
        
    def generate_question(self, topic: str) -> CulturalQuestion:
        # Prepara il prompt per il LLM
        prompt = f"""Genera una domanda culturale in italiano sul seguente argomento: {topic}.
        La domanda deve essere interessante, specifica e stimolante.
        Rispondi SOLO con la domanda, senza altri commenti."""
        
        # Chiamata al LLM (Ollama)
        response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,  # Risposta completa, non streaming
                    "options": {
                        "temperature": 0.7,    # Controllo della creatività (0.0-1.0)
                        "top_p": 0.9,          # Sampling per varietà nelle risposte
                        "max_tokens": 200,      # Lunghezza massima della risposta
                        #"stop": ["\n\n"]       # Ferma la generazione ai doppi newline
                    }
                },
                timeout=120,  # Timeout della richiesta in secondi
            )
        question_text = response.json()["response"].strip()
        
        # Crea e salva la domanda nel database
        question = CulturalQuestion(
            topic=topic,
            question=question_text
        )
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        
        return question
    
    def evaluate_answer(self, question_id: int, answer_text: str) -> QuestionAnswer:
        # Recupera la domanda
        question = self.db.query(CulturalQuestion).filter(CulturalQuestion.id == question_id).first()
        if not question:
            raise ValueError("Domanda non trovata")
            
        # Prepara il prompt per il LLM
        prompt = f"""Valuta la seguente risposta alla domanda culturale:

        Domanda: {question.question}
        Risposta: {answer_text}

        Fornisci una valutazione da 1 a 5 e una breve spiegazione in italiano.
        Rispondi nel seguente formato:
        Voto: [numero da 1 a 5]
        Spiegazione: [la tua spiegazione]"""
        
        # Chiamata al LLM
        response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,  # Risposta completa, non streaming
                    "options": {
                        "temperature": 0.7,    # Controllo della creatività (0.0-1.0)
                        "top_p": 0.9,          # Sampling per varietà nelle risposte
                        "max_tokens": 200,      # Lunghezza massima della risposta
                        #"stop": ["\n\n"]       # Ferma la generazione ai doppi newline
                    }
                },
                timeout=120,  # Timeout della richiesta in secondi
            )
        
        eval_text = response.json()["response"]
        
        # Estrai il voto e la spiegazione
        try:
            lines = eval_text.split("\n")
            score = float(lines[0].split(":")[1].strip())
            explanation = lines[1].split(":")[1].strip()
        except:
            score = 1.0
            explanation = "Errore nel formato della valutazione"
        
        # Crea e salva la risposta nel database
        answer = QuestionAnswer(
            question_id=question_id,
            answer_text=answer_text,
            score=score,
            evaluation=explanation
        )
        self.db.add(answer)
        self.db.commit()
        self.db.refresh(answer)
        
        return answer 