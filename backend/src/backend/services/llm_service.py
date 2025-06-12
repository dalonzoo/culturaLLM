# Importazioni necessarie per il servizio LLM
import requests  # Per le chiamate HTTP a Ollama
import os       # Per accedere alle variabili d'ambiente
import json     # Per la gestione dei dati JSON
from typing import Optional, Dict  # Per il type hinting

# Configurazione del servizio Ollama tramite variabili d'ambiente
# Se non specificate, usa i valori di default per lo sviluppo locale
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2:2b")

class LLMService:
    """
    Servizio per l'interazione con il modello linguistico Ollama.
    Gestisce la generazione di risposte alle domande sulla cultura italiana.
    """
    
    def __init__(self):
        """
        Inizializza il servizio LLM con l'host e il modello configurati.
        Usa i valori delle variabili d'ambiente o i default se non specificati.
        """
        self.host = OLLAMA_HOST
        self.model = OLLAMA_MODEL
        self.api_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
    
    def _generate_response(self, prompt: str) -> str:
        response = requests.post(
            self.api_url,
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
        )
        return response.json()["response"]

    def generate_question(self, theme: str, theme_description: str = "") -> str:
        """
        Genera una domanda culturale basata sul tema fornito
        """
        context = f"Tema: {theme}\n"
        if theme_description:
            context += f"Descrizione: {theme_description}\n"
        
        prompt = f"""
        {context}
        Sei un esperto di cultura italiana. Genera una domanda culturale specifica e interessante 
        sull'Italia relativa al tema fornito. La domanda deve:
        1. Essere specifica e richiedere conoscenze culturali dettagliate
        2. Non essere troppo generica o ovvia
        3. Essere formulata in modo chiaro e conciso
        4. Essere in italiano
        
        Rispondi SOLO con la domanda, senza altri commenti o spiegazioni.
        """
        
        return self._generate_response(prompt)

    def generate_answer(self, question: str, cultural_context: str = "") -> str:
        """
        Genera una risposta esperta alla domanda culturale
        """
        context = f"Contesto culturale: {cultural_context}\n" if cultural_context else ""
        
        prompt = f"""
        {context}
        Domanda: {question}
        
        Sei un esperto di cultura italiana. Fornisci una risposta dettagliata e accurata 
        alla domanda culturale. La risposta deve:
        1. Essere precisa e basata su fatti culturali
        2. Includere dettagli specifici e rilevanti
        3. Essere chiara e ben strutturata
        4. Essere in italiano
        
        Rispondi in modo naturale e informativo, come un esperto che spiega a un interessato.
        """
        
        return self._generate_response(prompt)

    def validate_answer(
        self,
        question_text: str,
        user_answer: str,
        correct_answer: str,
        cultural_context: str = ""
    ) -> Dict[str, any]:
        """
        Valida la risposta dell'utente confrontandola con la risposta corretta
        """
        context = f"Contesto culturale: {cultural_context}\n" if cultural_context else ""
        
        prompt = f"""
        {context}
        Domanda: {question_text}
        
        Risposta dell'utente: {user_answer}
        
        Risposta corretta: {correct_answer}
        
        Sei un esperto di cultura italiana e devi valutare la risposta dell'utente.
        Confronta la risposta dell'utente con quella corretta e fornisci:
        1. Un giudizio booleano sulla correttezza (true/false)
        2. Un feedback costruttivo che spieghi perché la risposta è corretta o cosa manca
        
        Rispondi in formato JSON con questa struttura:
        {{
            "is_correct": true/false,
            "feedback": "il tuo feedback qui"
        }}
        """
        
        response = self._generate_response(prompt)
        try:
            # Assicurati che la risposta sia in formato JSON valido
            result = json.loads(response)
            return result
        except:
            # Se il parsing JSON fallisce, fornisci una risposta di fallback
            return {
                "is_correct": False,
                "feedback": "Mi dispiace, non sono riuscito a valutare la risposta correttamente. Per favore, riprova."
            }

    def is_available(self) -> bool:
        """
        Verifica se il servizio LLM è disponibile e risponde.
        
        Returns:
            True se il servizio è attivo e risponde, False altrimenti
        """
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=10)
            return response.status_code == 200
        except:
            return False

# Istanza globale del servizio
# Viene utilizzata in tutta l'applicazione per accedere al servizio LLM
llm_service = LLMService()
