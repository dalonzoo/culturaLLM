# Importazioni necessarie per il servizio LLM
import boto3 # Importa la libreria AWS SDK
import os       # Per accedere alle variabili d'ambiente
import json     # Per la gestione dei dati JSON
from typing import Optional  # Per il type hinting

# Configurazione dell'endpoint SageMaker tramite variabili d'ambiente
# Assicurati che queste variabili siano impostate nell'ambiente o in Docker
SAGEMAKER_ENDPOINT_NAME = os.getenv("SAGEMAKER_ENDPOINT_NAME", "jumpstart-dft-hf-llm-gemma-2-2b-20250702-143618")
AWS_REGION = os.getenv("AWS_REGION", "eu-north-1")

class LLMService:
    """
    Servizio per l'interazione con il modello linguistico su AWS SageMaker.
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
    
    def generate_answer(self, question: str, cultural_context: str = "") -> str:
        """
        Genera una risposta a una domanda culturale utilizzando il modello LLM su SageMaker.
        
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
            # Payload per l'endpoint SageMaker (formato per Llama/Gemma)
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 200,      # Lunghezza massima della risposta
                    "top_p": 0.9,          # Sampling per varietà nelle risposte
                    "temperature": 0.7     # Controllo della creatività (0.0-1.0)
                }
            }
            
            # Chiamata all'endpoint SageMaker
            response = self.sagemaker_runtime.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType="application/json",
                Body=json.dumps(payload)
            )
            
            # Estrae e pulisce la risposta dal JSON
            result = json.loads(response["Body"].read().decode("utf-8"))
            
            # Assumiamo che la risposta sia nel formato [{"generated_text": "..."}]
            response_text = result[0]["generated_text"].strip()
            
            # Rimuove gli asterischi dalla risposta (se presenti)
            response_text = response_text.replace('*', '')
            return response_text
            
        except Exception as e:
            # Gestione degli errori durante l'invocazione dell'endpoint
            print(f"Error calling SageMaker LLM: {e}")
            return "Mi dispiace, non riesco a rispondere in questo momento."
    
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
        Rispondi esclusivamente con il tag (massimo 3 parole), SENZA alcun testo aggiuntivo, introduzione o punteggiatura finale. SOLO il TAG.
        Affermazione: {question}
        """
        try:
            # Payload per l'endpoint SageMaker (formato per Llama/Gemma)
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 15,  # Aumento leggermente per lasciare spazio
                    "top_p": 0.8,
                    "temperature": 0.3
                }
            }
            
            # Chiamata all'endpoint SageMaker
            response = self.sagemaker_runtime.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType="application/json",
                Body=json.dumps(payload)
            )
            
            # Estrae e pulisce la risposta dal JSON
            result = json.loads(response["Body"].read().decode("utf-8"))
            
            # Assumiamo che la risposta sia nel formato [{"generated_text": "..."}]
            response_text = result[0]["generated_text"].strip()
            
            # Rimuove gli asterischi dalla risposta (se presenti)
            response_text = response_text.replace('*', '')

            # Safeguard: Tronca il tag per assicurarti che non superi la lunghezza della colonna (es. 100 caratteri)
            if len(response_text) > 90: # Lascio un piccolo buffer
                response_text = response_text[:90]
                # Tenta di troncare all'ultima parola completa per una migliore leggibilità
                last_space = response_text.rfind(' ')
                if last_space != -1:
                    response_text = response_text[:last_space]
                response_text = response_text.strip()

            return response_text
            
        except Exception as e:
            print(f"Error calling SageMaker LLM for tag: {e}")
            return "Tag non disponibile"

# Istanza globale del servizio
# Viene utilizzata in tutta l'applicazione per accedere al servizio LLM
llm_service = LLMService()
