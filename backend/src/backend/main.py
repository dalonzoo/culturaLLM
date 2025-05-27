from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
import os

from backend.services.database import get_db, engine, Base
from backend.routers import auth, question, answer, validate, leaderboard
from backend.models.schemas import UserCreate, UserLogin, Token

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CulturaLLM API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(question.router, prefix="/api/questions", tags=["questions"])
app.include_router(answer.router, prefix="/api/answers", tags=["answers"])
app.include_router(validate.router, prefix="/api/validate", tags=["validate"])
app.include_router(leaderboard.router, prefix="/api/leaderboard", tags=["leaderboard"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "CulturaLLM API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
