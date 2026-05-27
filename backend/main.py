from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from datetime import datetime, timedelta, timezone, date
from typing import Optional, Literal
from fastapi import Query
import os
import re
from database import get_db
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import secrets

# Konfiguracja
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("Brak SECRET_KEY w zmiennych środowiskowych!")
ALGORITHM = "HS256"
TOKEN_WAZNOSC_GODZINY = 8

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/swagger-token")

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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

class ResetHaslaRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def waliduj_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not REGEX_EMAIL.match(v):
            raise ValueError("Nieprawidłowy format adresu email")
        return v


class NoweHasloRequest(BaseModel):
    token: str
    nowe_haslo: str




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
    telefon: Optional[str] = None
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

#Modele gabinet - dodawanie gabinetu
class DodajGabinetRequest(BaseModel):
    numer: str
    status: Literal["Dostępny", "Niedostępny"] = "Dostępny"

    @field_validator("numer")
    @classmethod
    def waliduj_numer(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Numer gabinetu jest wymagany")
        if len(v) > 10:
            raise ValueError("Numer gabinetu max 10 znaków")
        return v

class ZmienStatusGabinetuRequest(BaseModel):
    status: Literal["Dostępny", "Niedostępny"]

# modele grafik

class DodajGrafikRequest(BaseModel):
    lekarz_id: int = Field(gt=0)
    gabinet_id: int = Field(gt=0)
    data: date
    godzina_od: str   # format "HH:MM"
    godzina_do: str   # format "HH:MM"
    co_ile_minut: Literal[15, 20, 30, 45, 60] = 30 #domyslna wartosc 30 minut

    @model_validator(mode="after")
    def waliduj_terminy(self):
        #czy data z przyszłosci
        if self.data < date.today():
            raise ValueError("Data musi być dzisiejsza lub z przyszłości")
        # sprawdzanie godzin od i do
        regex_godziny = r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$"
        if not re.match(regex_godziny, self.godzina_od):
            raise ValueError("godzina_od musi być poprawną godziną w formacie HH:MM (00:00 - 23:59)")
        if not re.match(regex_godziny, self.godzina_do):
            raise ValueError("godzina_do musi być poprawną godziną w formacie HH:MM (00:00 - 23:59)")
        
        if self.godzina_od >= self.godzina_do:
            raise ValueError("godzina_od musi być wcześniejsza niż godzina_do")
        return self

# rezerwacja terminow
class RezerwacjaRequest(BaseModel):
    grafik_id: int = Field(gt=0)
    # pacjent_id pobierany z tokena chyba ze zalogowany jest adm lub rejestacja to:
    pacjent_id: Optional[int] = None


class AktualizacjaUzytkownikaRequest(BaseModel):
    rola: Optional[str] = None
    imie: Optional[str] = None
    nazwisko: Optional[str] = None
    telefon: Optional[str] = None
    # Pacjent
    miejscowosc: Optional[str] = None
    kod_pocztowy: Optional[str] = None
    ulica: Optional[str] = None
    nr_domu: Optional[str] = None
    nr_lokalu: Optional[str] = None
    # Lekarz
    specjalizacje_ids: Optional[list[int]] = None
    placowka_id: Optional[int] = None
    status_npwz: Optional[str] = None
    waznosc_oc: Optional[str] = None





# ======== HELPERY ========

def stworz_token(dane: dict) -> str:
    payload = dane.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=TOKEN_WAZNOSC_GODZINY)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# Helper — weryfikacja roli z tokena
def weryfikuj_token(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Nieprawidłowy token")


def tylko_admin(token: str = Depends(oauth2_scheme)) -> dict:
    payload = weryfikuj_token(token)
    if payload.get("rola") != "admin":
        raise HTTPException(status_code=403, detail="Brak uprawnień — wymagana rola admin")
    return payload

# helper do harmonogramu, gabinetu itd. tylko dla admina i pracownika rejestracji
def tylko_admin_lub_rejestracja(token: str = Depends(oauth2_scheme)) -> dict:
    payload = weryfikuj_token(token)
    if payload.get("rola") not in ["admin", "rejestracja"]:
        raise HTTPException(status_code=403, detail="Brak uprawnień")
    return payload

# helper do rezerwacji
def kazdy_zalogowany(token: str = Depends(oauth2_scheme)) -> dict:
    return weryfikuj_token(token)



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

    #do przechowywania imienia i nazwiska w tokenie - niezaleznie od roli
    imie, nazwisko = None, None
    if wynik.rola_nazwa == "pacjent":
        profil=db.execute(text("SELECT imie, nazwisko FROM pacjenci WHERE uzytkownik_id = :uid"), {"uid": wynik.id}).fetchone()
        if profil:
            imie, nazwisko = profil.imie, profil.nazwisko
    elif wynik.rola_nazwa == "lekarz":
        profil=db.execute(text("SELECT imie, nazwisko FROM lekarze WHERE uzytkownik_id = :uid"), {"uid": wynik.id}).fetchone()
        if profil:
            imie, nazwisko = profil.imie, profil.nazwisko
    elif wynik.rola_nazwa in ["admin", "rejestracja"]:
        profil=db.execute(text("SELECT imie, nazwisko FROM pracownicy WHERE uzytkownik_id = :uid"), {"uid": wynik.id}).fetchone()
        if profil:
            imie, nazwisko = profil.imie, profil.nazwisko

    token = stworz_token({
        "sub": wynik.email,
        "id": wynik.id,
        "rola": wynik.rola_nazwa,
        "imie": imie,
        "nazwisko": nazwisko
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "uzytkownik": {
            "id": wynik.id,
            "email": wynik.email,
            "rola": wynik.rola_nazwa,
            "profil_uzupelniony": wynik.profil_uzupelniony,
            "imie": imie,
            "nazwisko": nazwisko
        }
    }

# endpoint dla autoryzacji w swaggerze
@app.post("/api/auth/swagger-token", include_in_schema=False)
def swagger_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    zapytanie_sql = text("""
        SELECT u.id, u.email, u.haslo_hash, r.nazwa AS rola_nazwa
        FROM uzytkownicy u
        JOIN role r ON u.rola_id = r.id
        WHERE u.email = :email
    """)
    wynik = db.execute(zapytanie_sql, {"email": form_data.username}).fetchone()

    if not wynik or not pwd_context.verify(form_data.password, wynik.haslo_hash):
        raise HTTPException(status_code=401, detail="Nieprawidłowy email lub hasło")

    token = stworz_token({
        "sub": wynik.email,
        "id": wynik.id,
        "rola": wynik.rola_nazwa,
    })
    
    return {"access_token": token, "token_type": "bearer"}


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

@app.post("/api/forgot-password", status_code=200)
async def zapomniane_haslo(request: ResetHaslaRequest, db: Session = Depends(get_db)):
    uzytkownik = db.execute(
        text("SELECT id, email FROM uzytkownicy WHERE email = :email"),
        {"email": request.email}
    ).fetchone()

    # Zawsze zwracamy sukces — nie zdradzamy czy email istnieje
    if not uzytkownik:
        return {"status": "sukces"}

    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(minutes=15)

    db.execute(text("""
        UPDATE uzytkownicy 
        SET reset_token = :token, reset_token_expires = :expires
        WHERE id = :id
    """), {"token": token, "expires": expires, "id": uzytkownik.id})
    db.commit()

    link = f"http://localhost:5173/reset-password?token={token}"

    message = MessageSchema(
        subject="Reset hasła — MediSync",
        recipients=[uzytkownik.email],
        body=f"""
        <h2>Reset hasła MediSync</h2>
        <p>Otrzymaliśmy prośbę o reset hasła dla Twojego konta.</p>
        <p>Kliknij poniższy link aby ustawić nowe hasło:</p>
        <a href="{link}" style="
            display: inline-block;
            padding: 12px 24px;
            background-color: #3b82f6;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
        ">Resetuj hasło</a>
        <p>Link jest ważny przez <strong>15 minut</strong>.</p>
        <p>Jeśli nie prosiłeś o reset hasła, zignoruj tę wiadomość.</p>
        <br>
        <p>Zespół MediSync</p>
        """,
        subtype="html"
    )

    await fastmail.send_message(message)
    return {"status": "sukces"}


@app.post("/api/reset-password", status_code=200)
def reset_hasla(request: NoweHasloRequest, db: Session = Depends(get_db)):
    uzytkownik = db.execute(text("""
        SELECT id FROM uzytkownicy 
        WHERE reset_token = :token 
        AND reset_token_expires > :teraz
    """), {"token": request.token, "teraz": datetime.utcnow()}).fetchone()

    if not uzytkownik:
        raise HTTPException(status_code=400, detail="Token jest nieprawidłowy lub wygasł")

    if len(request.nowe_haslo) < 12:
        raise HTTPException(status_code=422, detail="Hasło musi mieć co najmniej 12 znaków")

    nowy_hash = pwd_context.hash(request.nowe_haslo)

    db.execute(text("""
        UPDATE uzytkownicy 
        SET haslo_hash = :hash, reset_token = NULL, reset_token_expires = NULL
        WHERE id = :id
    """), {"hash": nowy_hash, "id": uzytkownik.id})
    db.commit()

    return {"status": "sukces"}


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

# ======== ENDPOINTY GABINETY ========

#POBARANIE LISTY GABINETOW
@app.get("/api/reception/gabinety")
def lista_gabinetow(
    db: Session = Depends(get_db),
    payload: dict = Depends(tylko_admin_lub_rejestracja)
):
    wyniki = db.execute(text("SELECT id, numer, status FROM gabinety ORDER BY numer")).fetchall()
    return {"gabinety": [{"id": w.id, "numer": w.numer, "status": w.status} for w in wyniki]}

#DODAWANIE GABINETU
@app.post("/api/reception/gabinety", status_code=201)
def dodaj_gabinet(
    request: DodajGabinetRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(tylko_admin_lub_rejestracja)
):
    try:
        # sprawdzanie czy gabinet o tym nr istnieje
        istniejacy = db.execute(text("SELECT id FROM gabinety WHERE numer = :numer"), {"numer": request.numer}).fetchone()

        if istniejacy:
            raise HTTPException(status_code=409, detail="Gabinet o tym numerze już istnieje")

        # dodawanie nowego gabinetu - nie istneje
        nowy_gabinet = db.execute(text("""
            INSERT INTO gabinety (numer, status)
            VALUES (:numer, :status)
            RETURNING id
        """), {
            "numer": request.numer,
            "status": request.status,
        }).fetchone()

        db.commit()

        return {
            "status": "sukces",
            "gabinet_id": nowy_gabinet.id,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Błąd podczas dodawania gabinetu: {str(e)}")

#ZMIANA STATUSU GABINETU
@app.patch("/api/reception/gabinety/{gabinet_id}/status")
def zmien_status_gabinetu(
    gabinet_id: int,
    request: ZmienStatusGabinetuRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(tylko_admin_lub_rejestracja)
):
    try:
        # sprawdzanie czy gabinet istnieje
        gabinet = db.execute(text("SELECT id FROM gabinety WHERE id = :id"), {"id": gabinet_id}).fetchone()

        if not gabinet:
            raise HTTPException(status_code=404, detail="Podany gabinet nie istnieje")

        # aktualizacja statusu gabinetu
        db.execute(text("""
            UPDATE gabinety
            SET status = :status
            WHERE id = :id
        """), {
            "status": request.status,
            "id": gabinet_id,
        })

        db.commit()

        return {
            "status": "sukces",
            "wiadomosc": f"Status gabinetu {gabinet_id} został zmieniony na {request.status}",
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Błąd podczas zmiany statusu gabinetu: {str(e)}")

# ======== ENDPOINTY GRAFIK ========

@app.get("/api/reception/lekarze")
def lista_lekarzy(
    db: Session = Depends(get_db),
    payload: dict = Depends(tylko_admin_lub_rejestracja)
):
    wyniki = db.execute(text("""
        SELECT 
            l.id, 
            l.imie, 
            l.nazwisko, 
            array_remove(array_agg(s.nazwa), NULL) AS specjalizacje
        FROM lekarze l
        JOIN uzytkownicy u ON l.uzytkownik_id = u.id
        LEFT JOIN lekarz_specjalizacja ls ON l.id = ls.lekarz_id
        LEFT JOIN specjalizacje s ON ls.specjalizacja_id = s.id
        GROUP BY l.id, l.imie, l.nazwisko
        ORDER BY l.nazwisko, l.imie""")).fetchall()
    return {
        "lekarze": [
            {
                "id": w.id,
                "imie": w.imie,
                "nazwisko": w.nazwisko,
                "specjalizacje": w.specjalizacje
            }
            for w in wyniki
        ]
    }

@app.get("/api/reception/grafiki")
def lista_grafiku(
    data: date = Query(..., description="Data w formacie YYYY-MM-DD"),
    db: Session = Depends(get_db),
    payload: dict = Depends(tylko_admin_lub_rejestracja)
):
    wyniki = db.execute(text("""
        SELECT 
            gp.id, 
            l.imie AS lekarz_imie, 
            l.nazwisko AS lekarz_nazwisko, 
            g.numer AS gabinet_numer, 
            gp.termin_od, 
            gp.termin_do, 
            CASE WHEN w.id IS NOT NULL THEN true ELSE false END AS zajety
        FROM grafiki_pracy gp
        JOIN lekarze l ON gp.lekarz_id = l.id
        JOIN gabinety g ON gp.gabinet_id = g.id
        LEFT JOIN wizyty w ON w.grafik_id = gp.id
        WHERE DATE(gp.termin_od) = :data
        ORDER BY gp.termin_od, l.nazwisko"""), {"data": data}).fetchall()
    return {
        "grafiki": [
            {
                "id": w.id,
                "lekarz": f"{w.lekarz_imie} {w.lekarz_nazwisko}",
                "gabinet": w.gabinet_numer,
                "termin_od": w.termin_od,
                "termin_do": w.termin_do,
                "zajety": w.zajety
            }
            for w in wyniki
        ]
    }

    


@app.post("/api/reception/grafiki", status_code=201)
def dodaj_grafik(
    request: DodajGrafikRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(tylko_admin_lub_rejestracja)
):
    try:
        # 1. Parsowanie czasu z Pydantic do obiektów datetime
        h_od, m_od = map(int, request.godzina_od.split(":"))
        h_do, m_do = map(int, request.godzina_do.split(":"))

        poczatek_bloku = datetime(request.data.year, request.data.month, request.data.day, h_od, m_od)
        koniec_bloku = datetime(request.data.year, request.data.month, request.data.day, h_do, m_do)

        # 2. Inżynierska optymalizacja (1 zapytanie zamiast pętli zapytań)
        # Sprawdzamy, czy CAŁY zadeklarowany blok czasu koliduje z czymś w bazie
        kolizja = db.execute(text("""
            SELECT id FROM grafiki_pracy
            WHERE (lekarz_id = :lekarz_id OR gabinet_id = :gabinet_id)
            AND termin_od < :koniec_bloku
            AND termin_do > :poczatek_bloku
            LIMIT 1
        """), {
            "lekarz_id": request.lekarz_id,
            "gabinet_id": request.gabinet_id,
            "poczatek_bloku": poczatek_bloku,
            "koniec_bloku": koniec_bloku
        }).fetchone()

        if kolizja:
            raise HTTPException(
                status_code=409, 
                detail="Wykryto kolizję! Lekarz lub gabinet jest już zajęty w tym przedziale czasowym."
            )

        # 3. Generowanie slotów (logika w pamięci RAM, bardzo szybka)
        sloty = []
        aktualny = poczatek_bloku
        krok = timedelta(minutes=request.co_ile_minut)

        while aktualny + krok <= koniec_bloku:
            sloty.append({
                "lekarz_id": request.lekarz_id,
                "gabinet_id": request.gabinet_id,
                "termin_od": aktualny,
                "termin_do": aktualny + krok
            })
            aktualny += krok

        if not sloty:
            raise HTTPException(status_code=400, detail="Przedział czasu jest za krótki, aby wygenerować chociaż jeden slot.")

        # 4. Batch Insert (wstawienie całej listy słowników jednym uderzeniem do bazy)
        db.execute(text("""
            INSERT INTO grafiki_pracy (lekarz_id, gabinet_id, termin_od, termin_do)
            VALUES (:lekarz_id, :gabinet_id, :termin_od, :termin_do)
        """), sloty)

        db.commit()

        return {
            "status": "sukces",
            "dodano_slotow": len(sloty)
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Błąd podczas generowania grafiku: {str(e)}")


@app.delete("/api/reception/grafiki/{grafik_id}")
def usun_slot_grafiku(
    grafik_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(tylko_admin_lub_rejestracja)
):
    try:
        # 1. Sprawdź, czy slot istnieje
        slot = db.execute(
            text("SELECT id FROM grafiki_pracy WHERE id = :id"), 
            {"id": grafik_id}
        ).fetchone()
        
        if not slot:
            raise HTTPException(status_code=404, detail="Podany slot nie istnieje")

        # 2. Sprawdź powiązane wizyty (Integralność danych)
        wizyta = db.execute(
            text("SELECT id FROM wizyty WHERE grafik_id = :grafik_id"), 
            {"grafik_id": grafik_id}
        ).fetchone()
        
        if wizyta:
            raise HTTPException(status_code=409, detail="Nie można usunąć — slot ma już przypisaną wizytę!")

        # 3. Bezpieczne usunięcie
        db.execute(
            text("DELETE FROM grafiki_pracy WHERE id = :id"), 
            {"id": grafik_id}
        )
        
        db.commit()

        return {"status": "sukces", "wiadomosc": "Slot został pomyślnie usunięty"}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Błąd podczas usuwania slotu: {str(e)}")

@app.get("/api/admin/user/{user_id}")
def pobierz_uzytkownika(
    user_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(tylko_admin)
):
    uzytkownik = db.execute(text("""
        SELECT u.id, u.email, u.profil_uzupelniony,
               r.nazwa AS rola
        FROM uzytkownicy u
        JOIN role r ON u.rola_id = r.id
        WHERE u.id = :id
    """), {"id": user_id}).fetchone()

    if not uzytkownik:
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")

    dane = {
        "id": uzytkownik.id,
        "email": uzytkownik.email,
        "rola": uzytkownik.rola,
        "profil_uzupelniony": uzytkownik.profil_uzupelniony,
        "profil": None,
    }

    if uzytkownik.rola == "pacjent":
        profil = db.execute(text("""
            SELECT p.imie, p.nazwisko, p.pesel, p.telefon,
                   a.miejscowosc, a.kod_pocztowy, a.ulica, a.nr_domu, a.nr_lokalu
            FROM pacjenci p
            LEFT JOIN adresy a ON p.adres_id = a.id
            WHERE p.uzytkownik_id = :id
        """), {"id": user_id}).fetchone()

        if profil:
            dane["profil"] = {
                "imie": profil.imie, "nazwisko": profil.nazwisko,
                "pesel": profil.pesel, "telefon": profil.telefon,
                "miejscowosc": profil.miejscowosc, "kod_pocztowy": profil.kod_pocztowy,
                "ulica": profil.ulica, "nr_domu": profil.nr_domu, "nr_lokalu": profil.nr_lokalu,
            }

    elif uzytkownik.rola == "lekarz":
        profil = db.execute(text("""
            SELECT l.imie, l.nazwisko, l.pesel, l.npwz, l.status_npwz,
                   l.waznosc_oc, l.placowka_id, p.nazwa AS placowka_nazwa
            FROM lekarze l
            LEFT JOIN placowki p ON l.placowka_id = p.id
            WHERE l.uzytkownik_id = :id
        """), {"id": user_id}).fetchone()

        specjalizacje = db.execute(text("""
            SELECT s.id, s.nazwa
            FROM specjalizacje s
            JOIN lekarz_specjalizacja ls ON s.id = ls.specjalizacja_id
            JOIN lekarze l ON ls.lekarz_id = l.id
            WHERE l.uzytkownik_id = :id
        """), {"id": user_id}).fetchall()

        if profil:
            dane["profil"] = {
                "imie": profil.imie, "nazwisko": profil.nazwisko,
                "pesel": profil.pesel, "npwz": profil.npwz,
                "status_npwz": profil.status_npwz,
                "waznosc_oc": str(profil.waznosc_oc),
                "placowka_id": profil.placowka_id,
                "placowka_nazwa": profil.placowka_nazwa,
                "specjalizacje": [{"id": s.id, "nazwa": s.nazwa} for s in specjalizacje],
            }

    elif uzytkownik.rola == "pracownik":
        profil = db.execute(text("""
            SELECT imie, nazwisko, telefon, pesel
            FROM pracownicy WHERE uzytkownik_id = :id
        """), {"id": user_id}).fetchone()

        if profil:
            dane["profil"] = {
                "imie": profil.imie, "nazwisko": profil.nazwisko,
                "telefon": profil.telefon, "pesel": profil.pesel,
            }

    return dane


@app.put("/api/admin/user/{user_id}", status_code=200)
def aktualizuj_uzytkownika(
    user_id: int,
    request: AktualizacjaUzytkownikaRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(tylko_admin)
):
    uzytkownik = db.execute(text("""
        SELECT u.id, r.nazwa AS rola
        FROM uzytkownicy u
        JOIN role r ON u.rola_id = r.id
        WHERE u.id = :id
    """), {"id": user_id}).fetchone()

    if not uzytkownik:
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")

    # Zmiana roli
    if request.rola and request.rola != uzytkownik.rola:
        nowa_rola = db.execute(
            text("SELECT id FROM role WHERE nazwa = :nazwa"),
            {"nazwa": request.rola}
        ).fetchone()
        if not nowa_rola:
            raise HTTPException(status_code=404, detail="Rola nie istnieje")
        db.execute(text("""
            UPDATE uzytkownicy SET rola_id = :rola_id WHERE id = :id
        """), {"rola_id": nowa_rola.id, "id": user_id})

    rola = request.rola or uzytkownik.rola

    # Aktualizacja profilu pacjenta
    if rola == "pacjent":
        pacjent = db.execute(
            text("SELECT id, adres_id FROM pacjenci WHERE uzytkownik_id = :id"),
            {"id": user_id}
        ).fetchone()

        if pacjent:
            if request.telefon:
                db.execute(text("""
                    UPDATE pacjenci SET telefon = :telefon WHERE uzytkownik_id = :id
                """), {"telefon": request.telefon, "id": user_id})

            if any([request.miejscowosc, request.kod_pocztowy,
                    request.ulica, request.nr_domu, request.nr_lokalu]):
                db.execute(text("""
                    UPDATE adresy SET
                        miejscowosc = COALESCE(:miejscowosc, miejscowosc),
                        kod_pocztowy = COALESCE(:kod_pocztowy, kod_pocztowy),
                        ulica = COALESCE(:ulica, ulica),
                        nr_domu = COALESCE(:nr_domu, nr_domu),
                        nr_lokalu = COALESCE(:nr_lokalu, nr_lokalu)
                    WHERE id = :adres_id
                """), {
                    "miejscowosc": request.miejscowosc,
                    "kod_pocztowy": request.kod_pocztowy,
                    "ulica": request.ulica,
                    "nr_domu": request.nr_domu,
                    "nr_lokalu": request.nr_lokalu,
                    "adres_id": pacjent.adres_id,
                })

    # Aktualizacja profilu lekarza
    elif rola == "lekarz":
        lekarz = db.execute(
            text("SELECT id FROM lekarze WHERE uzytkownik_id = :id"),
            {"id": user_id}
        ).fetchone()

        if lekarz:
            if request.status_npwz or request.waznosc_oc or request.placowka_id:
                db.execute(text("""
                    UPDATE lekarze SET
                        status_npwz = COALESCE(:status_npwz, status_npwz),
                        waznosc_oc = COALESCE(:waznosc_oc::date, waznosc_oc),
                        placowka_id = COALESCE(:placowka_id, placowka_id)
                    WHERE id = :id
                """), {
                    "status_npwz": request.status_npwz,
                    "waznosc_oc": request.waznosc_oc,
                    "placowka_id": request.placowka_id,
                    "id": lekarz.id,
                })

            if request.specjalizacje_ids is not None:
                db.execute(text("""
                    DELETE FROM lekarz_specjalizacja WHERE lekarz_id = :id
                """), {"id": lekarz.id})
                for spec_id in request.specjalizacje_ids:
                    db.execute(text("""
                        INSERT INTO lekarz_specjalizacja (lekarz_id, specjalizacja_id)
                        VALUES (:lekarz_id, :spec_id)
                        ON CONFLICT DO NOTHING
                    """), {"lekarz_id": lekarz.id, "spec_id": spec_id})

    # Aktualizacja pracownika
    elif rola == "pracownik":
        if request.telefon:
            db.execute(text("""
                UPDATE pracownicy SET telefon = :telefon WHERE uzytkownik_id = :id
            """), {"telefon": request.telefon, "id": user_id})

    db.commit()
    return {"status": "sukces"}

# ======ENDPOINTY REZERWACJA WIZYT=======


# 1. lista specjalizacji
@app.get("/api/specjalizacje/lista")
def lista_specjalizacji(db: Session = Depends(get_db), payload: dict = Depends(kazdy_zalogowany)):
    wyniki = db.execute(text("SELECT id, nazwa FROM specjalizacje ORDER BY nazwa")).fetchall()
    return {"specjalizacje": [{"id": w.id, "nazwa": w.nazwa} for w in wyniki]}


# 2. lista lekarzy + opcjonalnie filtr po specjalizacji
@app.get("/api/lekarze/lista")
def lista_lekarzy(
    specjalizacja_id: Optional[int] = None, 
    db: Session = Depends(get_db), 
    payload: dict = Depends(kazdy_zalogowany)
):
    zapytanie_sql = """
        SELECT 
            l.id, l.imie, l.nazwisko, 
            array_remove(array_agg(s.nazwa), NULL) AS specjalizacje
        FROM lekarze l
        LEFT JOIN lekarz_specjalizacja ls ON l.id = ls.lekarz_id
        LEFT JOIN specjalizacje s ON ls.specjalizacja_id = s.id
    """
    parametry = {}
    
    if specjalizacja_id:
        zapytanie_sql += " WHERE l.id IN (SELECT lekarz_id FROM lekarz_specjalizacja WHERE specjalizacja_id = :spec_id)"
        parametry["spec_id"] = specjalizacja_id
        
    zapytanie_sql += " GROUP BY l.id, l.imie, l.nazwisko ORDER BY l.nazwisko, l.imie"
    wyniki = db.execute(text(zapytanie_sql), parametry).fetchall()
    
    return {
        "lekarze": [
            {
                "id": w.id,
                "imie": w.imie,
                "nazwisko": w.nazwisko,
                "specjalizacje": w.specjalizacje,
                "placowka": "Przychodnia MediSync"
            }
            for w in wyniki
        ]
    }


# 3. szukanie wolnych slotow
@app.get("/api/wizyty/wolne-sloty")
def wolne_sloty_lekarza(
    lekarz_id: int, 
    data: date, 
    db: Session = Depends(get_db), 
    payload: dict = Depends(kazdy_zalogowany)
):
    if data < date.today():
        raise HTTPException(status_code=400, detail="Nie można wyszukiwać terminów w przeszłości.")

    # Dodane podzapytanie (subquery) wyciągające cenę z cennika na podstawie specjalizacji lekarza
    zapytanie = text("""
        SELECT gp.id, gp.termin_od, gp.termin_do, g.numer AS gabinet_numer,
               (
                   SELECT c.cena 
                   FROM cennik c
                   JOIN lekarz_specjalizacja ls ON ls.lekarz_id = gp.lekarz_id
                   WHERE c.specjalizacja_id = ls.specjalizacja_id
                   AND (c.data_do IS NULL OR c.data_do > NOW())
                   ORDER BY c.id
                   LIMIT 1
               ) AS cena
        FROM grafiki_pracy gp
        JOIN gabinety g ON gp.gabinet_id = g.id
        LEFT JOIN wizyty w ON gp.id = w.grafik_id AND w.status = 'Zaplanowana'
        WHERE gp.lekarz_id = :lekarz_id AND DATE(gp.termin_od) = :data
        AND w.id IS NULL AND gp.termin_od > NOW()
        ORDER BY gp.termin_od
    """)
    wyniki = db.execute(zapytanie, {"lekarz_id": lekarz_id, "data": data}).fetchall()
    
    return {
        "sloty": [
            {
                "id": w.id,
                "termin_od": w.termin_od.isoformat(),
                "termin_do": w.termin_do.isoformat(),
                "gabinet_numer": w.gabinet_numer,
                "cena": float(w.cena) if w.cena else None  # Zwracamy cenę jako liczbę
            } for w in wyniki
        ]
    }

# wyszukiwanie pacjentów przy rezerwacji wizyty (dla pracownikow rejestracji, admin tez ma dostep)
@app.get("/api/pacjenci/szukaj")
def szukaj_pacjentow(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
    payload: dict = Depends(tylko_admin_lub_rejestracja)
):
    wyniki = db.execute(text("""
        SELECT p.id, p.imie, p.nazwisko, p.pesel, p.telefon
        FROM pacjenci p
        WHERE p.imie ILIKE :q
           OR p.nazwisko ILIKE :q
           OR p.pesel LIKE :q_exact
           OR CONCAT(p.imie, ' ', p.nazwisko) ILIKE :q
        ORDER BY p.nazwisko, p.imie
        LIMIT 10
    """), {"q": f"%{q}%", "q_exact": f"{q}%"}).fetchall()
    
    return {
        "pacjenci": [
            {
                "id": w.id, 
                "imie": w.imie, 
                "nazwisko": w.nazwisko, 
                "pesel": w.pesel, 
                "telefon": w.telefon
            }
            for w in wyniki
        ]
    }


# 4. rezerwacja wizyty z FOR UPDATE NOWAIT
@app.post("/api/wizyty")
def zarezerwuj_wizyte(
    request: RezerwacjaRequest, 
    db: Session = Depends(get_db), 
    payload: dict = Depends(kazdy_zalogowany)
):
    rola = payload.get("rola")
    
    if rola == "pacjent":
        pacjent = db.execute(text("SELECT id FROM pacjenci WHERE uzytkownik_id = :uid"), {"uid": payload.get("id")}).fetchone()
        if not pacjent:
            raise HTTPException(404, "Nie znaleziono profilu pacjenta.")
        pacjent_id = pacjent.id
    elif rola in ["admin", "rejestracja"]:
        if not request.pacjent_id:
            raise HTTPException(422, "Rejestracja musi podać pacjent_id.")
        pacjent_id = request.pacjent_id
    else:
        raise HTTPException(403, "Brak uprawnień do rezerwacji.")

    try:
        # LOCK - FOR UPDATE NOWAIT
        slot = db.execute(text("""
            SELECT gp.id, gp.termin_od, l.imie, l.nazwisko, g.numer as gabinet 
            FROM grafiki_pracy gp
            JOIN lekarze l ON gp.lekarz_id = l.id
            JOIN gabinety g ON gp.gabinet_id = g.id
            WHERE gp.id = :grafik_id FOR UPDATE NOWAIT
        """), {"grafik_id": request.grafik_id}).fetchone()
        
        if not slot:
            raise HTTPException(404, "Nie znaleziono slotu.")

        zajety = db.execute(text("SELECT id FROM wizyty WHERE grafik_id = :grafik_id AND status = 'Zaplanowana'"), {"grafik_id": request.grafik_id}).fetchone()
        if zajety:
            raise HTTPException(409, "Ten slot jest już zajęty.")

        # przekazanie parametru do zapytania o cennik
        # dobieranie cennika po specjalizacji lekarza
        cennik = db.execute(text("""
            SELECT c.id, c.cena FROM cennik c
            JOIN lekarz_specjalizacja ls ON ls.specjalizacja_id = c.specjalizacja_id
            WHERE ls.lekarz_id = (
                SELECT lekarz_id FROM grafiki_pracy WHERE id = :grafik_id
            )
            AND (c.data_do IS NULL OR c.data_do > NOW())
            ORDER BY c.id
            LIMIT 1
        """), {"grafik_id": request.grafik_id}).fetchone()

        # fallback — specjalizacja bez cennika → Wizyta ogólna
        if not cennik:
            cennik = db.execute(text("""
                SELECT id, cena FROM cennik
                WHERE specjalizacja_id IS NULL
                AND (data_do IS NULL OR data_do > NOW())
                LIMIT 1
            """)).fetchone()

        if not cennik:
            raise HTTPException(status_code=500, detail="Błąd systemu: Brak cennika dla tej specjalizacji.")

        result = db.execute(text("""
            INSERT INTO wizyty (pacjent_id, grafik_id, cennik_id, status)
            VALUES (:pacjent_id, :grafik_id, :cennik_id, 'Zaplanowana')
            RETURNING id
        """), {
            "pacjent_id": pacjent_id,
            "grafik_id": request.grafik_id,
            "cennik_id": cennik.id
        })
        nowa_wizyta_id = result.fetchone()[0]
        db.commit()

        return {
            "status": "sukces",
            "wizyta_id": nowa_wizyta_id,
            "termin": slot.termin_od.isoformat(),
            "lekarz": f"{slot.imie} {slot.nazwisko}",
            "gabinet": slot.gabinet
        }
        
    except OperationalError as e:
        db.rollback()
        if "could not obtain lock" in str(e).lower() or "nowait" in str(e).lower():
            raise HTTPException(status_code=409, detail="Ten slot jest właśnie rezerwowany przez kogoś innego. Spróbuj ponownie za chwilę.")
        raise HTTPException(status_code=500, detail=f"Błąd bazy danych: {str(e)}")
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Błąd serwera: {str(e)}")


# lista wizyt pacjenta
@app.get("/api/wizyty/moje")
def moje_wizyty(db: Session = Depends(get_db), payload: dict = Depends(kazdy_zalogowany)):
    if payload.get("rola") != "pacjent":
        raise HTTPException(403, "Tylko pacjent może przeglądać listę wizyt.")
        
    pacjent = db.execute(text("SELECT id FROM pacjenci WHERE uzytkownik_id = :uid"), {"uid": payload.get("id")}).fetchone()
    
    if not pacjent:
        raise HTTPException(status_code=404, detail="Nie znaleziono profilu pacjenta.")
    
    zapytanie = text("""
        SELECT 
            w.id, w.status, gp.termin_od, gp.termin_do,
            l.imie AS lekarz_imie, l.nazwisko AS lekarz_nazwisko,
            g.numer AS gabinet, c.cena,
            array_remove(array_agg(s.nazwa), NULL) AS specjalizacje
        FROM wizyty w
        JOIN grafiki_pracy gp ON w.grafik_id = gp.id
        JOIN lekarze l ON gp.lekarz_id = l.id
        JOIN gabinety g ON gp.gabinet_id = g.id
        JOIN cennik c ON w.cennik_id = c.id
        LEFT JOIN lekarz_specjalizacja ls ON l.id = ls.lekarz_id
        LEFT JOIN specjalizacje s ON ls.specjalizacja_id = s.id
        WHERE w.pacjent_id = :pacjent_id
        GROUP BY w.id, w.status, gp.termin_od, gp.termin_do, l.imie, l.nazwisko, g.numer, c.cena
        ORDER BY gp.termin_od DESC
    """)
    wyniki = db.execute(zapytanie, {"pacjent_id": pacjent.id}).fetchall()
    
    return {
        "wizyty": [
            {
                "id": w.id,
                "status": w.status,
                "termin_od": w.termin_od.isoformat(),
                "termin_do": w.termin_do.isoformat(),
                "lekarz_imie": w.lekarz_imie,
                "lekarz_nazwisko": w.lekarz_nazwisko,
                "specjalizacje": w.specjalizacje,
                "gabinet": w.gabinet,
                "cena": f"{w.cena:.2f}"
            } for w in wyniki
        ]
    }


# odwolywanie wizyty
@app.delete("/api/wizyty/{wizyta_id}")
def odwolaj_wizyte(wizyta_id: int, db: Session = Depends(get_db), payload: dict = Depends(kazdy_zalogowany)):
    wizyta = db.execute(text("""
        SELECT w.id, w.pacjent_id, gp.termin_od, w.status 
        FROM wizyty w JOIN grafiki_pracy gp ON w.grafik_id = gp.id WHERE w.id = :wizyta_id
    """), {"wizyta_id": wizyta_id}).fetchone()
    
    if not wizyta:
        raise HTTPException(404, "Nie znaleziono wizyty.")
        
    if payload.get("rola") == "pacjent":
        pacjent = db.execute(text("SELECT id FROM pacjenci WHERE uzytkownik_id = :uid"), {"uid": payload.get("id")}).fetchone()
        if not pacjent or wizyta.pacjent_id != pacjent.id:
            raise HTTPException(403, "Nie masz uprawnień.")
        
        # zabezpieczenie przed bledem stre czasowych - czas wizyty z aktualnym czasem serwera
        now_time = datetime.now(timezone.utc) if wizyta.termin_od.tzinfo else datetime.now()
        if wizyta.termin_od <= now_time + timedelta(hours=24):
            raise HTTPException(409, "Odwołanie możliwe tylko 24h przed terminem.")
            
    if wizyta.status == "Odwołana":
        raise HTTPException(400, "Już odwołana.")
        
    try:
        db.execute(text("UPDATE wizyty SET status = 'Odwołana' WHERE id = :wizyta_id"), {"wizyta_id": wizyta_id})
        db.commit()
        return {"status": "sukces", "wiadomosc": "Wizyta została odwołana."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Błąd podczas odwoływania wizyty: {str(e)}")


# pojedyczna rezerwacja szczegoly
@app.get("/api/wizyty/{wizyta_id}")
def szczegoly_wizyty(wizyta_id: int, db: Session = Depends(get_db), payload: dict = Depends(kazdy_zalogowany)):
    zapytanie = text("""
        SELECT w.id, w.status, w.pacjent_id, gp.termin_od, gp.termin_do,
               l.imie AS lekarz_imie, l.nazwisko AS lekarz_nazwisko, g.numer AS gabinet
        FROM wizyty w
        JOIN grafiki_pracy gp ON w.grafik_id = gp.id
        JOIN lekarze l ON gp.lekarz_id = l.id
        JOIN gabinety g ON gp.gabinet_id = g.id
        WHERE w.id = :wizyta_id
    """)
    wizyta = db.execute(zapytanie, {"wizyta_id": wizyta_id}).fetchone()
    
    if not wizyta:
        raise HTTPException(404, "Nie znaleziono wizyty.")
        
    if payload.get("rola") == "pacjent":
        pacjent = db.execute(text("SELECT id FROM pacjenci WHERE uzytkownik_id = :uid"), {"uid": payload.get("id")}).fetchone()
        if not pacjent or wizyta.pacjent_id != pacjent.id:
            raise HTTPException(403, "Brak dostępu.")

    return {
        "id": wizyta.id,
        "status": wizyta.status,
        "termin_od": wizyta.termin_od.isoformat(),
        "termin_do": wizyta.termin_do.isoformat(),
        "lekarz": f"{wizyta.lekarz_imie} {wizyta.lekarz_nazwisko}",
        "gabinet": wizyta.gabinet
    }


