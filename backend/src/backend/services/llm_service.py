# Importazioni necessarie per il servizio LLM
import requests  # Per le chiamate HTTP a Ollama
import os       # Per accedere alle variabili d'ambiente
import json     # Per la gestione dei dati JSON
from typing import Optional  # Per il type hinting

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
    
    def generate_answer(self, question: str, cultural_context: str = "") -> str:
        """
        Genera una risposta a una domanda culturale utilizzando il modello LLM.
        
        Args:
            question: La domanda posta dall'utente
            cultural_context: Contesto culturale aggiuntivo (opzionale)
            
        Returns:
            La risposta generata dal modello, o un messaggio di errore in caso di problemi
        """
        
        # Costruzione del prompt con istruzioni specifiche per il modello
        prompt = f"""
        Sei un assistente esperto nella cultura italiana. Rispondi alla seguente domanda in modo accurato e culturalmente appropriato.Non dare risposte troppo lunghe.
        Importante che la risposta sia umana e naturale senza markdown,'*' o formattazioni particolari o suddivisioni in paragrafi, quindi tutto in un unico paragrafo.
        Importante che non si capisca che è la risposta di un modello LLM.
        Contesto culturale: {cultural_context}
        
        Domanda: {question}
        
        Rispondi in italiano in modo naturale e informativo:
        """
        
        try:
            # Chiamata API a Ollama per la generazione della risposta
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
            response.raise_for_status()  # Solleva eccezione per errori HTTP
            
            # Estrae e pulisce la risposta dal JSON
            result = response.json()
            response_text = result.get("response", "").strip()
            # Rimuove gli asterischi dalla risposta
            response_text = response_text.replace('*', '')
            return response_text
            
        except requests.exceptions.RequestException as e:
            # Gestione degli errori di rete o del servizio
            print(f"Error calling LLM: {e}")
            return "Mi dispiace, non riesco a rispondere in questo momento."
    
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

    def generate_tag(self, question: str) -> str:
        """
        Genera un tag riassuntivo (max 3 parole) per una domanda usando il modello LLM.
        Args:
            question: La domanda da riassumere
        Returns:
            Un tag di massimo 3 parole
        """
        prompt = f"""
        Leggi attentamente la seguente affermazione. 
        Genera un singolo tag che ne rappresenti al meglio il significato o l'argomento principale. 
        Non deve essere un riassunto della domanda, ma deve solo prendere in considerazione l'argomento principale.
        Cerca di usare parole che sono utilizzate già nella affermazione senza crearne altre.
        Il tag deve essere composto da massimo 3 parole, ma usa meno parole possibile (preferibilmente una o due parole, solo raramente tre se strettamente necessario).
        Il tag deve essere sintetico, rappresentativo e privo di spiegazioni o punteggiatura.
        Rispondi esclusivamente con il tag, senza testo aggiuntivo.
        Affermazione: {question}
        """
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.8,
                        "max_tokens": 10
                    }
                },
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()
        except requests.exceptions.RequestException as e:
            print(f"Error calling LLM for tag: {e}")
            return "Tag non disponibile"

# Istanza globale del servizio
# Viene utilizzata in tutta l'applicazione per accedere al servizio LLM
llm_service = LLMService()
