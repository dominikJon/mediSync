import os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from fastapi_mail import FastMail, ConnectionConfig

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("Brak SECRET_KEY w zmiennych środowiskowych!")
ALGORITHM = "HS256"
TOKEN_WAZNOSC_GODZINY = 8

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/swagger-token")

# Konfiguracja FastMail
mail_config = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
    MAIL_FROM=os.getenv("MAIL_FROM", "noreply@medisync.pl"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 1025)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "mailpit"),
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=False,
)
fastmail = FastMail(mail_config)

def stworz_token(dane: dict) -> str:
    payload = dane.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=TOKEN_WAZNOSC_GODZINY)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def weryfikuj_token(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Nieprawidłowy token")

def kazdy_zalogowany(token: str = Depends(oauth2_scheme)) -> dict:
    return weryfikuj_token(token)

def tylko_admin(token: str = Depends(oauth2_scheme)) -> dict:
    payload = weryfikuj_token(token)
    if payload.get("rola") != "admin":
        raise HTTPException(status_code=403, detail="Brak uprawnień — wymagana rola admin")
    return payload

def tylko_lekarz(token: str = Depends(oauth2_scheme)) -> dict:
    payload = weryfikuj_token(token)
    if payload.get("rola") != "lekarz":
        raise HTTPException(status_code=403, detail="Brak uprawnień — wymagana rola lekarz")
    return payload

def tylko_admin_lub_rejestracja(token: str = Depends(oauth2_scheme)) -> dict:
    payload = weryfikuj_token(token)
    if payload.get("rola") not in ["admin", "rejestracja"]:
        raise HTTPException(status_code=403, detail="Brak uprawnień")
    return payload

def tylko_pacjent(token: str = Depends(oauth2_scheme)) -> dict:
    payload = weryfikuj_token(token)
    if payload.get("rola") != "pacjent":
        raise HTTPException(status_code=403, detail="Brak uprawnień — wymagana rola pacjent")
    return payload