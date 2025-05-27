from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://culturallm_user:culturallm_pass@localhost:3307/culturallm")

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from backend.models.schemas import Base

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
