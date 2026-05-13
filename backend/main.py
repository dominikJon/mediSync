from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from database import get_db

 # ── Konfiguracja ──────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("Brak SECRET_KEY w zmiennych środowiskowych!")
ALGORITHM = "HS256"
TOKEN_WAZNOSC_GODZINY = 8
 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
 
app = FastAPI()

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Port Vite — zmień na produkcyjny URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Modele ────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    haslo: str
 
 
# ── Helpery ───────────────────────────────────────────────────────────────────
def stworz_token(dane: dict) -> str:
    payload = dane.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=TOKEN_WAZNOSC_GODZINY)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
 
 
# ── Endpointy ─────────────────────────────────────────────────────────────────
@app.post("/api/login")
def logowanie(request: LoginRequest, db: Session = Depends(get_db)):
    # Raw SQL z parametryzowanym zapytaniem (zabezpieczenie przed SQL Injection)
    zapytanie_sql = text("""
        SELECT u.id, u.email, u.haslo_hash, r.nazwa AS rola_nazwa
        FROM uzytkownicy u
        JOIN role r ON u.rola_id = r.id
        WHERE u.email = :email
    """)
 
    wynik = db.execute(zapytanie_sql, {"email": request.email}).fetchone()
 
    # Ten sam komunikat błędu dla złego emaila i złego hasła —
    # nie zdradzamy, które z nich jest niepoprawne (zabezpieczenie przed enumeration)
    if not wynik:
        raise HTTPException(status_code=401, detail="Nieprawidłowy email lub hasło")
 
    if not pwd_context.verify(request.haslo, wynik.haslo_hash):
        raise HTTPException(status_code=401, detail="Nieprawidłowy email lub hasło")
 
    # Generujemy JWT z danymi użytkownika
    token = stworz_token({
        "sub": wynik.email,
        "id": wynik.id,
        "rola": wynik.rola_nazwa,
    })
 
    return {
        "access_token": token,
        "token_type": "bearer",
        "uzytkownik": {
            "id": wynik.id,
            "email": wynik.email,
            "rola": wynik.rola_nazwa,
        }
    }
 