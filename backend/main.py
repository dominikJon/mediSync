from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os
from database import get_db

 #Konfiguracja
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("Brak SECRET_KEY w zmiennych środowiskowych!")
ALGORITHM = "HS256"
TOKEN_WAZNOSC_GODZINY = 8
 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
 
app = FastAPI()

#CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Port Vite — zmień na produkcyjny URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Modele
class LoginRequest(BaseModel):
    email: str
    haslo: str

class RejestracjaRequest(BaseModel):
        email: str
        haslo: str

@app.post("/api/register", status_code=201)
def rejestracja(request: RejestracjaRequest, db: Session = Depends(get_db)):
    sprawdz_email = text("SELECT id FROM uzytkownicy WHERE email = :email")
    istniejacy = db.execute(sprawdz_email, {"email": request.email}).fetchone()

    if istniejacy:
        raise HTTPException(status_code=409, detail="Konto z tym adresem email już istnieje")

    rola = db.execute(text("SELECT id FROM role WHERE nazwa = 'pacjent'")).fetchone()

    if not rola:
        raise HTTPException(status_code=500, detail="Błąd konfiguracji: brak roli 'pacjent' w bazie")

    haslo_hash = pwd_context.hash(request.haslo)

    nowy_uzytkownik = text("""
        INSERT INTO uzytkownicy (email, haslo_hash, rola_id)
        VALUES (:email, :haslo_hash, :rola_id)
        RETURNING id, email
    """)

    wynik = db.execute(nowy_uzytkownik, {
        "email": request.email,
        "haslo_hash": haslo_hash,
        "rola_id": rola.id,
    }).fetchone()

    db.commit()

    return {
        "status": "sukces",
        "uzytkownik": {
            "id": wynik.id,
            "email": wynik.email,
        }
    }
 
 
#Helpery 
def stworz_token(dane: dict) -> str:
    payload = dane.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=TOKEN_WAZNOSC_GODZINY)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
 
 
#Endpointy 
@app.post("/api/login")
def logowanie(request: LoginRequest, db: Session = Depends(get_db)):
    # Raw SQL z parametryzowanym zapytaniem (zabezpieczenie przed SQL Injection)
    zapytanie_sql = text("""
        SELECT u.id, u.email, u.haslo_hash, u.profil_uzupelniony, r.nazwa AS rola_nazwa
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
            "profil_uzupelniony": wynik.profil_uzupelniony,
        }
    }

    
    class KartotekaRequest(BaseModel):
    imie: str
    nazwisko: str
    pesel: str
    telefon: str
    miejscowosc: str
    kod_pocztowy: str
    ulica: str | None = None
    nr_domu: str
    nr_lokalu: str | None = None
    brak_ulicy: bool = False

@app.post("/api/complete-profile", status_code=200)
def uzupelnij_kartoteke(request: KartotekaRequest, db: Session = Depends(get_db)):
    # Walidacja PESEL — 11 cyfr
    if not request.pesel.isdigit() or len(request.pesel) != 11:
        raise HTTPException(status_code=422, detail="PESEL musi składać się z 11 cyfr")

    # Walidacja kodu pocztowego — format XX-XXX
    import re
    if not re.match(r"^\d{2}-\d{3}$", request.kod_pocztowy):
        raise HTTPException(status_code=422, detail="Kod pocztowy musi być w formacie XX-XXX")

    # Walidacja ulicy
    if not request.brak_ulicy and not request.ulica:
        raise HTTPException(status_code=422, detail="Podaj ulicę lub zaznacz 'brak ulicy'")

    # Sprawdź czy PESEL już istnieje
    istniejacy = db.execute(
        text("SELECT id FROM pacjenci WHERE pesel = :pesel"),
        {"pesel": request.pesel}
    ).fetchone()
    if istniejacy:
        raise HTTPException(status_code=409, detail="Pacjent z tym PESELem już istnieje")

    # Wstaw adres
    nowy_adres = db.execute(text("""
        INSERT INTO adresy (miejscowosc, kod_pocztowy, ulica, nr_domu, nr_lokalu)
        VALUES (:miejscowosc, :kod_pocztowy, :ulica, :nr_domu, :nr_lokalu)
        RETURNING id
    """), {
        "miejscowosc": request.miejscowosc,
        "kod_pocztowy": request.kod_pocztowy,
        "ulica": request.ulica if not request.brak_ulicy else None,
        "nr_domu": request.nr_domu,
        "nr_lokalu": request.nr_lokalu,
    }).fetchone()

    # Wstaw pacjenta — uzytkownik_id z tokena nie mamy jeszcze, 
    # tymczasowo pobieramy po emailu z requestu
    # TODO: zastąpić weryfikacją JWT
    db.execute(text("""
        INSERT INTO pacjenci (uzytkownik_id, adres_id, pesel, imie, nazwisko, telefon)
        VALUES (:uzytkownik_id, :adres_id, :pesel, :imie, :nazwisko, :telefon)
    """), {
        "uzytkownik_id": request.uzytkownik_id,
        "adres_id": nowy_adres.id,
        "pesel": request.pesel,
        "imie": request.imie,
        "nazwisko": request.nazwisko,
        "telefon": request.telefon,
    })

    # Oznacz profil jako uzupełniony
    db.execute(text("""
        UPDATE uzytkownicy SET profil_uzupelniony = TRUE
        WHERE id = :uzytkownik_id
    """), {"uzytkownik_id": request.uzytkownik_id})

    db.commit()

    return {"status": "sukces"}
 