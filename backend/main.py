from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy.orm import Session
from sqlalchemy import text
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone, date
from typing import Optional, Literal
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


# ======== HELPERY WALIDACYJNE ========

def waliduj_pesel(pesel: str) -> bool:
    """Walidacja PESEL z cyfrą kontrolną (algorytm)."""
    if not re.match(r"^\d{11}$", pesel):
        return False
    wagi = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
    suma = sum(w * int(pesel[i]) for i, w in enumerate(wagi))
    kontrolna = (10 - (suma % 10)) % 10
    return kontrolna == int(pesel[10])


REGEX_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
REGEX_LITERY_PL = re.compile(r"^[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ\s-]+$")
REGEX_TELEFON = re.compile(r"^(\+48)?\d{9}$")
REGEX_KOD_POCZTOWY = re.compile(r"^\d{2}-\d{3}$")
REGEX_NR_DOMU = re.compile(r"^[a-zA-Z0-9\-\/]+$")
REGEX_ZNAK_SPECJALNY = re.compile(r"[!@#$%^&*(),.?\":{}|<>_\-]")


# ======== MODELE Z WALIDACJĄ ========

class LoginRequest(BaseModel):
    email: str
    haslo: str

    @field_validator("email")
    @classmethod
    def waliduj_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not REGEX_EMAIL.match(v):
            raise ValueError("Nieprawidłowy format adresu email")
        return v

    @field_validator("haslo")
    @classmethod
    def waliduj_haslo_niepuste(cls, v: str) -> str:
        if not v:
            raise ValueError("Hasło jest wymagane")
        return v


class RejestracjaRequest(BaseModel):
    email: str
    haslo: str

    @field_validator("email")
    @classmethod
    def waliduj_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not REGEX_EMAIL.match(v):
            raise ValueError("Nieprawidłowy format adresu email")
        return v

    @field_validator("haslo")
    @classmethod
    def waliduj_haslo(cls, v: str) -> str:
        if len(v) < 12:
            raise ValueError("Hasło musi mieć co najmniej 12 znaków")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Hasło musi zawierać co najmniej jedną wielką literę")
        if not re.search(r"[a-z]", v):
            raise ValueError("Hasło musi zawierać co najmniej jedną małą literę")
        if not re.search(r"\d", v):
            raise ValueError("Hasło musi zawierać co najmniej jedną cyfrę")
        if not REGEX_ZNAK_SPECJALNY.search(v):
            raise ValueError("Hasło musi zawierać co najmniej jeden znak specjalny")
        return v


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

    @field_validator("imie", "nazwisko")
    @classmethod
    def waliduj_imie_nazwisko(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Musi mieć co najmniej 2 znaki")
        if not REGEX_LITERY_PL.match(v):
            raise ValueError("Dozwolone są tylko litery, spacja i myślnik")
        return v

    @field_validator("pesel")
    @classmethod
    def waliduj_pesel_field(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^\d{11}$", v):
            raise ValueError("PESEL musi składać się z dokładnie 11 cyfr")
        if not waliduj_pesel(v):
            raise ValueError("Nieprawidłowy PESEL — błędna cyfra kontrolna")
        return v

    @field_validator("telefon")
    @classmethod
    def waliduj_telefon(cls, v: str) -> str:
        v = v.replace(" ", "")
        if not REGEX_TELEFON.match(v):
            raise ValueError("Telefon: 9 cyfr lub +48 i 9 cyfr")
        return v

    @field_validator("miejscowosc")
    @classmethod
    def waliduj_miejscowosc(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Miejscowość musi mieć co najmniej 2 znaki")
        return v

    @field_validator("kod_pocztowy")
    @classmethod
    def waliduj_kod_pocztowy(cls, v: str) -> str:
        v = v.strip()
        if not REGEX_KOD_POCZTOWY.match(v):
            raise ValueError("Kod pocztowy musi być w formacie XX-XXX")
        return v

    @field_validator("nr_domu")
    @classmethod
    def waliduj_nr_domu(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Numer domu jest wymagany")
        if not REGEX_NR_DOMU.match(v):
            raise ValueError("Numer domu może zawierać tylko litery, cyfry, myślnik i ukośnik")
        return v

    @model_validator(mode="after")
    def waliduj_ulice(self):
        if not self.brak_ulicy:
            if not self.ulica or not self.ulica.strip():
                raise ValueError("Podaj ulicę lub zaznacz 'brak ulicy'")
            self.ulica = self.ulica.strip()
        else:
            self.ulica = None
        return self


# Modele admina
class DodajLekarzaRequest(BaseModel):
    email: str
    haslo: str
    imie: str
    nazwisko: str
    pesel: Optional[str] = None
    brak_peselu: bool = False
    telefon: Optional[str] = None,
    npwz: str
    status_npwz: Literal["aktywny", "zawieszony", "wygasły"]
    waznosc_oc: date
    placowka_id: int = Field(gt=0)
    specjalizacje_ids: list[int] = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def waliduj_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not REGEX_EMAIL.match(v):
            raise ValueError("Nieprawidłowy format adresu email")
        return v

    @field_validator("haslo")
    @classmethod
    def waliduj_haslo(cls, v: str) -> str:
        if len(v) < 12:
            raise ValueError("Hasło musi mieć co najmniej 12 znaków")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Hasło musi zawierać co najmniej jedną wielką literę")
        if not re.search(r"[a-z]", v):
            raise ValueError("Hasło musi zawierać co najmniej jedną małą literę")
        if not re.search(r"\d", v):
            raise ValueError("Hasło musi zawierać co najmniej jedną cyfrę")
        if not REGEX_ZNAK_SPECJALNY.search(v):
            raise ValueError("Hasło musi zawierać co najmniej jeden znak specjalny")
        return v

    @field_validator("imie", "nazwisko")
    @classmethod
    def waliduj_imie_nazwisko(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Musi mieć co najmniej 2 znaki")
        if not REGEX_LITERY_PL.match(v):
            raise ValueError("Dozwolone są tylko litery, spacja i myślnik")
        return v

    @field_validator("npwz")
    @classmethod
    def waliduj_npwz(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^\d{7}$", v):
            raise ValueError("NPWZ musi składać się z dokładnie 7 cyfr")
        return v

    @field_validator("waznosc_oc")
    @classmethod
    def waliduj_waznosc_oc(cls, v: date) -> date:
        if v <= date.today():
            raise ValueError("Data ważności OC musi być w przyszłości")
        return v

    @model_validator(mode="after")
    def waliduj_pesel_lub_brak(self):
        if self.brak_peselu:
            # Zagraniczny lekarz — ignorujemy PESEL całkowicie
            self.pesel = None
            return self

        # Krajowy lekarz — PESEL wymagany i poprawny
        if not self.pesel or not self.pesel.strip():
            raise ValueError("PESEL jest wymagany (lub zaznacz 'brak PESEL')")

        pesel_clean = self.pesel.strip()
        if not re.match(r"^\d{11}$", pesel_clean):
            raise ValueError("PESEL musi składać się z dokładnie 11 cyfr")
        if not waliduj_pesel(pesel_clean):
            raise ValueError("Nieprawidłowy PESEL — błędna cyfra kontrolna")

        self.pesel = pesel_clean
        return self

#Modele pracownikow
class DodajPracownika(BaseModel):
    email: str
    haslo: str
    imie: str
    nazwisko: str
    pesel: Optional[str] = None
    brak_peselu: bool = False
    telefon: str
    rola: Literal["admin", "rejestracja"]

    @field_validator("email")
    @classmethod
    def waliduj_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not REGEX_EMAIL.match(v):
            raise ValueError("Nieprawidłowy format adresu email")
        return v

    @field_validator("haslo")
    @classmethod
    def waliduj_haslo(cls, v: str) -> str:
        if len(v) < 12:
            raise ValueError("Hasło musi mieć co najmniej 12 znaków")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Hasło musi zawierać co najmniej jedną wielką literę")
        if not re.search(r"[a-z]", v):
            raise ValueError("Hasło musi zawierać co najmniej jedną małą literę")
        if not re.search(r"\d", v):
            raise ValueError("Hasło musi zawierać co najmniej jedną cyfrę")
        if not REGEX_ZNAK_SPECJALNY.search(v):
            raise ValueError("Hasło musi zawierać co najmniej jeden znak specjalny")
        return v

    @field_validator("imie", "nazwisko")
    @classmethod
    def waliduj_imie_nazwisko(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Musi mieć co najmniej 2 znaki")
        if not REGEX_LITERY_PL.match(v):
            raise ValueError("Dozwolone są tylko litery, spacja i myślnik")
        return v

    @field_validator("telefon")
    @classmethod
    def waliduj_telefon(cls, v: str) -> str:
        v = v.replace(" ", "")
        if not REGEX_TELEFON.match(v):
            raise ValueError("Telefon: 9 cyfr lub +48 i 9 cyfr")
        return v

    @model_validator(mode="after")
    def waliduj_pesel_lub_brak(self):
        if self.brak_peselu:
            self.pesel = None
            return self
        if not self.pesel or not self.pesel.strip():
            raise ValueError("PESEL jest wymagany (lub zaznacz 'brak PESEL')")
        pesel_clean = self.pesel.strip()
        if not re.match(r"^\d{11}$", pesel_clean):
            raise ValueError("PESEL musi składać się z dokładnie 11 cyfr")
        if not waliduj_pesel(pesel_clean):
            raise ValueError("Nieprawidłowy PESEL — błędna cyfra kontrolna")
        self.pesel = pesel_clean
        return self



# ======== HELPERY ========

def stworz_token(dane: dict) -> str:
    payload = dane.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=TOKEN_WAZNOSC_GODZINY)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


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


def tylko_admin(authorization: str = Header(default=None)) -> dict:
    payload = weryfikuj_token(authorization)
    if payload.get("rola") != "admin":
        raise HTTPException(status_code=403, detail="Brak uprawnień — wymagana rola admin")
    return payload


# ======== ENDPOINTY ========

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
        INSERT INTO uzytkownicy (email, haslo_hash, rola_id, profil_uzupelniony)
        VALUES (:email, :haslo_hash, :rola_id, FALSE)
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
        "ulica": request.ulica,
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


# ======== ENDPOINTY ADMINA ========

@app.get("/api/admin/users")
def lista_uzytkownikow(
    db: Session = Depends(get_db),
    payload: dict = Depends(tylko_admin)
):
    wyniki = db.execute(text("""
        SELECT 
            u.id, 
            u.email, 
            u.profil_uzupelniony, 
            r.nazwa AS rola,
            COALESCE(p.imie, l.imie, pr.imie) AS imie,
            COALESCE(p.nazwisko, l.nazwisko, pr.nazwisko) AS nazwisko
        FROM uzytkownicy u
        JOIN role r ON u.rola_id = r.id
        LEFT JOIN pacjenci p ON u.id = p.uzytkownik_id
        LEFT JOIN lekarze l ON u.id = l.uzytkownik_id
        LEFT JOIN pracownicy pr ON u.id = pr.uzytkownik_id
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
    try:
        # Sprawdź czy email zajęty
        if db.execute(text("SELECT id FROM uzytkownicy WHERE email = :email"),
                      {"email": request.email}).fetchone():
            raise HTTPException(status_code=409, detail="Email już istnieje")

        # Sprawdź czy NPWZ zajęty
        if db.execute(text("SELECT id FROM lekarze WHERE npwz = :npwz"),
                      {"npwz": request.npwz}).fetchone():
            raise HTTPException(status_code=409, detail="Lekarz z tym NPWZ już istnieje")

        # Sprawdź unikalność PESEL (tylko dla lekarzy z PESELem)
        if not request.brak_peselu and request.pesel:
            if db.execute(text("SELECT id FROM lekarze WHERE pesel = :pesel"),
                          {"pesel": request.pesel}).fetchone():
                raise HTTPException(status_code=409, detail="Lekarz z tym PESELem już istnieje")

        # Sprawdź czy placówka istnieje
        if not db.execute(text("SELECT id FROM placowki WHERE id = :id"),
                          {"id": request.placowka_id}).fetchone():
            raise HTTPException(status_code=404, detail="Placówka nie istnieje")

        # Sprawdź czy wszystkie specjalizacje istnieją
        for spec_id in request.specjalizacje_ids:
            if not db.execute(text("SELECT id FROM specjalizacje WHERE id = :id"),
                              {"id": spec_id}).fetchone():
                raise HTTPException(status_code=404, detail=f"Specjalizacja o id {spec_id} nie istnieje")

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
            INSERT INTO lekarze (uzytkownik_id, placowka_id, imie, nazwisko, pesel, npwz, status_npwz, waznosc_oc, telefon)
            VALUES (:uzytkownik_id, :placowka_id, :imie, :nazwisko, :pesel, :npwz, :status_npwz, :waznosc_oc, :telefon)
            RETURNING id
        """), {
            "uzytkownik_id": nowy_user.id,
            "placowka_id": request.placowka_id,
            "imie": request.imie,
            "nazwisko": request.nazwisko,
            "pesel": request.pesel,
            "npwz": request.npwz,
            "status_npwz": request.status_npwz,
            "waznosc_oc": request.waznosc_oc,
            "telefon": request.telefon,
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

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Błąd podczas dodawania lekarza: {str(e)}")


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

@app.post("/api/admin/add-staff", status_code=201)
def dodaj_pracownika(
    request: DodajPracownika,
    db: Session = Depends(get_db),
    payload: dict = Depends(tylko_admin)
):
    try:
        # Sprawdź czy email zajęty
        if db.execute(text("SELECT id FROM uzytkownicy WHERE email = :email"),
                    {"email": request.email}).fetchone():
            raise HTTPException(status_code=409, detail="Email już istnieje")

        # Sprawdź unikalność PESEL (tylko dla lekarzy z PESELem)
        if not request.brak_peselu and request.pesel:
            if db.execute(text("SELECT id FROM pracownicy WHERE pesel = :pesel"),
                        {"pesel": request.pesel}).fetchone():
                raise HTTPException(status_code=409, detail="Pracownik z tym PESELem już istnieje")

        # Pobierz rolę lekarza
        rola = db.execute(
            text("SELECT id FROM role WHERE nazwa = :nazwa"),
            {"nazwa": request.rola}
            ).fetchone()
        if not rola:
            raise HTTPException(status_code=500, detail=f"Brak roli '{request.rola}' w bazie")

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

        # Utwórz profil pracownika
        nowy_pracownik = db.execute(text("""
            INSERT INTO pracownicy (uzytkownik_id, imie, nazwisko, pesel, telefon)
            VALUES (:uzytkownik_id, :imie, :nazwisko, :pesel, :telefon)
            RETURNING id
        """), {
            "uzytkownik_id": nowy_user.id,
            "imie": request.imie,
            "nazwisko": request.nazwisko,
            "pesel": request.pesel,
            "telefon": request.telefon,
        }).fetchone()

        db.commit()

        return {
            "status": "sukces",
            "pracownik_id": nowy_pracownik.id,
            "uzytkownik_id": nowy_user.id,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Błąd podczas dodawania pracownika: {str(e)}")