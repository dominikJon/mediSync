from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from typing import Optional
import os
import re
from database import get_db

# Konfiguracja
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("Brak SECRET_KEY w zmiennych środowiskowych!")
ALGORITHM = "HS256"
TOKEN_WAZNOSC_GODZINY = 8

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modele
class LoginRequest(BaseModel):
    email: str
    haslo: str

class RejestracjaRequest(BaseModel):
    email: str
    haslo: str

class KartotekaRequest(BaseModel):
    uzytkownik_id: int
    imie: str
    nazwisko: str
    pesel: str
    telefon: str
    miejscowosc: str
    kod_pocztowy: str
    ulica: Optional[str] = None
    nr_domu: str
    nr_lokalu: Optional[str] = None
    brak_ulicy: bool = False

# Helpery
def stworz_token(dane: dict) -> str:
    payload = dane.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=TOKEN_WAZNOSC_GODZINY)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# Endpointy
@app.post("/api/login")
def logowanie(request: LoginRequest, db: Session = Depends(get_db)):
    zapytanie_sql = text("""
        SELECT u.id, u.email, u.haslo_hash, u.profil_uzupelniony, r.nazwa AS rola_nazwa
        FROM uzytkownicy u
        JOIN role r ON u.rola_id = r.id
        WHERE u.email = :email
    """)

    wynik = db.execute(zapytanie_sql, {"email": request.email}).fetchone()

    if not wynik:
        raise HTTPException(status_code=401, detail="Nieprawidłowy email lub hasło")

    if not pwd_context.verify(request.haslo, wynik.haslo_hash):
        raise HTTPException(status_code=401, detail="Nieprawidłowy email lub hasło")

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

    wynik = db.execute(text("""
        INSERT INTO uzytkownicy (email, haslo_hash, rola_id)
        VALUES (:email, :haslo_hash, :rola_id)
        RETURNING id, email
    """), {
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


@app.post("/api/complete-profile", status_code=200)
def uzupelnij_kartoteke(request: KartotekaRequest, db: Session = Depends(get_db)):
    # Walidacja PESEL
    if not request.pesel.isdigit() or len(request.pesel) != 11:
        raise HTTPException(status_code=422, detail="PESEL musi składać się z 11 cyfr")

    # Walidacja kodu pocztowego
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

    # Wstaw pacjenta
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


# Modele admina
class DodajLekarzaRequest(BaseModel):
    email: str
    haslo: str
    npwz: str
    status_npwz: str
    waznosc_oc: str  # format YYYY-MM-DD
    placowka_id: int
    specjalizacje_ids: list[int]


# Helper — weryfikacja roli z tokena
def weryfikuj_token(authorization: str = None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Brak tokena autoryzacyjnego")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Nieprawidłowy token")


from fastapi import Header

def tylko_admin(authorization: str = Header(default=None)) -> dict:
    payload = weryfikuj_token(authorization)
    if payload.get("rola") != "admin":
        raise HTTPException(status_code=403, detail="Brak uprawnień — wymagana rola admin")
    return payload


# Endpointy admina
@app.get("/api/admin/users")
def lista_uzytkownikow(
    db: Session = Depends(get_db),
    payload: dict = Depends(tylko_admin)
):
    wyniki = db.execute(text("""
        SELECT u.id, u.email, u.profil_uzupelniony, r.nazwa AS rola,
               p.imie, p.nazwisko, p.pesel
        FROM uzytkownicy u
        JOIN role r ON u.rola_id = r.id
        LEFT JOIN pacjenci p ON u.id = p.uzytkownik_id
        ORDER BY u.id DESC
    """)).fetchall()

    return {
        "uzytkownicy": [
            {
                "id": w.id,
                "email": w.email,
                "rola": w.rola,
                "profil_uzupelniony": w.profil_uzupelniony,
                "imie": w.imie,
                "nazwisko": w.nazwisko,
                "pesel": w.pesel,
            }
            for w in wyniki
        ]
    }


@app.post("/api/admin/add-doctor", status_code=201)
def dodaj_lekarza(
    request: DodajLekarzaRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(tylko_admin)
):
    # Sprawdź czy email zajęty
    if db.execute(text("SELECT id FROM uzytkownicy WHERE email = :email"),
                  {"email": request.email}).fetchone():
        raise HTTPException(status_code=409, detail="Email już istnieje")

    # Sprawdź czy NPWZ zajęty
    if db.execute(text("SELECT id FROM lekarze WHERE npwz = :npwz"),
                  {"npwz": request.npwz}).fetchone():
        raise HTTPException(status_code=409, detail="Lekarz z tym NPWZ już istnieje")

    # Sprawdź czy placówka istnieje
    if not db.execute(text("SELECT id FROM placowki WHERE id = :id"),
                      {"id": request.placowka_id}).fetchone():
        raise HTTPException(status_code=404, detail="Placówka nie istnieje")

    # Pobierz rolę lekarza
    rola = db.execute(text("SELECT id FROM role WHERE nazwa = 'lekarz'")).fetchone()
    if not rola:
        raise HTTPException(status_code=500, detail="Brak roli 'lekarz' w bazie")

    # Utwórz konto użytkownika
    haslo_hash = pwd_context.hash(request.haslo)
    nowy_user = db.execute(text("""
        INSERT INTO uzytkownicy (email, haslo_hash, rola_id, profil_uzupelniony)
        VALUES (:email, :haslo_hash, :rola_id, TRUE)
        RETURNING id
    """), {
        "email": request.email,
        "haslo_hash": haslo_hash,
        "rola_id": rola.id,
    }).fetchone()

    # Utwórz profil lekarza
    nowy_lekarz = db.execute(text("""
        INSERT INTO lekarze (uzytkownik_id, placowka_id, npwz, status_npwz, waznosc_oc)
        VALUES (:uzytkownik_id, :placowka_id, :npwz, :status_npwz, :waznosc_oc)
        RETURNING id
    """), {
        "uzytkownik_id": nowy_user.id,
        "placowka_id": request.placowka_id,
        "npwz": request.npwz,
        "status_npwz": request.status_npwz,
        "waznosc_oc": request.waznosc_oc,
    }).fetchone()

    # Przypisz specjalizacje
    for spec_id in request.specjalizacje_ids:
        db.execute(text("""
            INSERT INTO lekarz_specjalizacja (lekarz_id, specjalizacja_id)
            VALUES (:lekarz_id, :specjalizacja_id)
        """), {
            "lekarz_id": nowy_lekarz.id,
            "specjalizacja_id": spec_id,
        })

    db.commit()

    return {
        "status": "sukces",
        "lekarz_id": nowy_lekarz.id,
        "uzytkownik_id": nowy_user.id,
    }


@app.get("/api/admin/placowki")
def lista_placowek(
    db: Session = Depends(get_db),
    payload: dict = Depends(tylko_admin)
):
    wyniki = db.execute(text("SELECT id, nazwa FROM placowki ORDER BY nazwa")).fetchall()
    return {"placowki": [{"id": w.id, "nazwa": w.nazwa} for w in wyniki]}


@app.get("/api/admin/specjalizacje")
def lista_specjalizacji(
    db: Session = Depends(get_db),
    payload: dict = Depends(tylko_admin)
):
    wyniki = db.execute(text("SELECT id, nazwa FROM specjalizacje ORDER BY nazwa")).fetchall()
    return {"specjalizacje": [{"id": w.id, "nazwa": w.nazwa} for w in wyniki]}