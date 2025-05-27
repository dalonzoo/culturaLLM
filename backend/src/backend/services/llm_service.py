import requests
import os
import json
from typing import Optional

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2:2b")

class LLMService:
    def __init__(self):
        self.host = OLLAMA_HOST
        self.model = OLLAMA_MODEL
    
    def generate_answer(self, question: str, cultural_context: str = "") -> str:
        """Generate an answer to a cultural question using the LLM"""
        
        prompt = f"""
        Sei un assistente esperto nella cultura italiana. Rispondi alla seguente domanda in modo accurato e culturalmente appropriato.
        
        Contesto culturale: {cultural_context}
        
        Domanda: {question}
        
        Rispondi in italiano in modo naturale e informativo:
        """
        
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 200
                    }
                },
                timeout=60,
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
            
        except requests.exceptions.RequestException as e:
            print(f"Error calling LLM: {e}")
            return "Mi dispiace, non riesco a rispondere in questo momento."
    
    def is_available(self) -> bool:
        """Check if the LLM service is available"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=10)
            return response.status_code == 200
        except:
            return False

# Global instance
llm_service = LLMService()
