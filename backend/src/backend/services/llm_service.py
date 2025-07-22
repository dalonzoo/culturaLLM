# Importazioni necessarie per il servizio LLM
import boto3 # Importa la libreria AWS SDK
import os       # Per accedere alle variabili d'ambiente
import json     # Per la gestione dei dati JSON
from typing import Optional, Dict  # Per il type hinting
import requests # Importa la libreria per le richieste HTTP

# Configurazione dell'endpoint SageMaker tramite variabili d'ambiente
# Assicurati che queste variabili siano impostate nell'ambiente o in Docker
SAGEMAKER_ENDPOINT_NAME = os.getenv("SAGEMAKER_ENDPOINT_NAME", "jumpstart-dft-hf-llm-gemma-2-2b-20250702-143618")
AWS_REGION = os.getenv("AWS_REGION", "eu-north-1")
MODAL_APP_URL = os.getenv("MODAL_APP_URL", "https://danieledalonzon03--culturallm-nlp-server-fastapi-app.modal.run")

class LLMService:
    """
    Servizio per l'interazione con il modello linguistico su AWS SageMaker e altri servizi esterni.
    Gestisce la generazione di risposte e tag culturali.
    """
    
    def __init__(self):
        """
        Inizializza il servizio LLM con il client SageMaker Runtime.
        Le credenziali AWS verranno caricate automaticamente dalle variabili d'ambiente
        o dal file di configurazione AWS CLI.
        """
        self.sagemaker_runtime = boto3.client("sagemaker-runtime", region_name=AWS_REGION)
        self.endpoint_name = SAGEMAKER_ENDPOINT_NAME
        self.modal_app_url = MODAL_APP_URL
    
    def generate_answer(self, question: str, cultural_context: str = "") -> str:
        """
        Genera una risposta a una domanda utilizzando il servizio esterno.
        Utilizza il livello di complessità 3 (medio).
        
        Args:
            question: La domanda o l'argomento su cui generare una risposta.
            cultural_context: Non utilizzato da questo endpoint, mantenuto per compatibilità.
            
        Returns:
            La risposta generata dal modello, o un messaggio di errore.
        """
        endpoint_url = f"{self.modal_app_url}/tasks/cyan"
        payload = {
            "argomento": question,
            "livello": "3"  # Livello medio come richiesto
        }
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(endpoint_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            answer = data.get("risposta", "Risposta non disponibile.").strip()
            
            # Pulisce la risposta da eventuali virgolette extra
            if answer.startswith('"') and answer.endswith('"'):
                answer = answer[1:-1]
            
            return answer

        except requests.exceptions.RequestException as e:
            print(f"Error calling Modal endpoint for answer generation: {e}")
            return "Mi dispiace, non riesco a rispondere in questo momento."
    
    def generate_tag(self, question: str) -> str:
        """
        Genera un tag riassuntivo per una domanda usando il servizio esterno.
        Args:
            question: La domanda da riassumere
        Returns:
            Una stringa contenente i tag generati.
        """
        endpoint_url = f"{self.modal_app_url}/tasks/orange"
        payload = {"question": question}
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(endpoint_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            tags_raw = data.get("tags", "Tag non disponibile").strip()

            # Importa i moduli necessari per il parsing
            import re
            import ast

            # Cerca una sottostringa che assomiglia a una lista Python (es. ['a', 'b'])
            match = re.search(r'\[.*\]', tags_raw)
            if match:
                list_str = match.group(0)
                try:
                    tags_list = ast.literal_eval(list_str)
                    if isinstance(tags_list, list):
                        # Formatta correttamente come "tag1,tag2,tag3"
                        return ",".join(str(t).strip() for t in tags_list)
                except (ValueError, SyntaxError) as e:
                    print(f"Parsing della lista di tag fallito: {e}. Si procede con il fallback.")
                    # Fallback: pulizia della stringa grezza se ast.literal_eval fallisce
                    cleaned_tags = list_str.replace("[", "").replace("]", "").replace("'", "").replace('"', "")
                    return ", ".join(tag.strip() for tag in cleaned_tags.split(","))

            # Se non trova una lista o il parsing fallisce, restituisce la stringa originale
            return tags_raw.replace("Tags:", "").strip()
            
        except requests.exceptions.RequestException as e:
            print(f"Error calling Modal endpoint for tag generation: {e}")
            return "Tag non disponibile"

    def validate_answer(self, question: str, answer: str, feedback: str = "") -> Optional[Dict]:
        """
        Valuta una risposta utilizzando il servizio esterno.
        Args:
            question: La domanda originale.
            answer: La risposta da valutare.
            feedback: Un eventuale feedback (opzionale).
        Returns:
            Un dizionario con i dati della validazione, o None in caso di errore.
        """
        endpoint_url = f"{self.modal_app_url}/tasks/red"
        payload = {
            "question": question,
            "answer": answer,
            "feedback": feedback or "Nessun feedback"  # Invia un placeholder se il feedback è vuoto
        }
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(endpoint_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error calling Modal endpoint for answer validation: {e}")
            return None

# Istanza globale del servizio
# Viene utilizzata in tutta l'applicazione per accedere al servizio LLM
llm_service = LLMService()
