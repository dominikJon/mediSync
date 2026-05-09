from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()
DB_PASSWORD = os.getenv("DB_PASSWORD")

if not DB_PASSWORD:
    raise ValueError("Nie można znaleźć hasła do bazy danych. Upewnij się, że plik .env zawiera DB_PASSWORD.")

SQLALCHEMY_DATABASE_URL = f"postgresql://admin:{DB_PASSWORD}@localhost:5432/medisync"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()