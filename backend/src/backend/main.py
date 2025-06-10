# Importazione delle dipendenze principali di FastAPI
# - FastAPI: framework principale
# - Depends: per le dipendenze tra funzioni
# - HTTPException: per gestire gli errori HTTP
# - status: costanti per i codici di stato HTTP
from fastapi import FastAPI, Depends, HTTPException, status

# Middleware per gestire le richieste CORS (Cross-Origin Resource Sharing)
from fastapi.middleware.cors import CORSMiddleware

# Classe per gestire l'autenticazione tramite token Bearer
from fastapi.security import HTTPBearer

# Importazione per gestire le sessioni del database
from sqlalchemy.orm import Session
import os

# Importazioni locali per la configurazione del database e i modelli
from backend.services.database import get_db, engine, Base

# Importazione di tutti i router dell'applicazione
from backend.routers import auth, question, answer, validate, leaderboard

# Importazione degli schemi Pydantic per la validazione dei dati
from backend.models.schemas import UserCreate, UserLogin, Token

# Creazione delle tabelle nel database se non esistono
# Questo comando utilizza i modelli SQLAlchemy per generare lo schema
Base.metadata.create_all(bind=engine)

# Inizializzazione dell'applicazione FastAPI con titolo e versione
app = FastAPI(title="CulturaLLM API", version="1.0.0")

# Configurazione del middleware CORS
# Permette le richieste da:
# - localhost:3000 (sviluppo locale)
# - frontend:3000 (container Docker)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000","http://0.0.0.0:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusione dei router per organizzare gli endpoint
# Ogni router gestisce una specifica area funzionale dell'API
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])                 # Gestione autenticazione
app.include_router(question.router, prefix="/api/questions", tags=["questions"])   # Gestione domande
app.include_router(answer.router, prefix="/api/answers", tags=["answers"])         # Gestione risposte
app.include_router(validate.router, prefix="/api/validate", tags=["validate"])     # Gestione validazioni
app.include_router(leaderboard.router, prefix="/api/leaderboard", tags=["leaderboard"]) # Gestione classifica

# Endpoint per il controllo dello stato dell'API
# Utilizzato per healthcheck e monitoraggio
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Endpoint root che conferma il funzionamento dell'API
@app.get("/")
async def root():
    return {"message": "CulturaLLM API is running"}

# Avvio del server se il file viene eseguito direttamente
if __name__ == "__main__":
    import uvicorn
    # Avvia il server sulla porta 5000, accessibile da qualsiasi indirizzo IP
    uvicorn.run(app, host="0.0.0.0", port=5000)
