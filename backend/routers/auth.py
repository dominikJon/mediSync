from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
import secrets

from database import get_db
from models.schemas import LoginRequest, RejestracjaRequest, ResetHaslaRequest, NoweHasloRequest, KartotekaRequest
from dependencies import pwd_context, stworz_token, fastmail
from fastapi_mail import MessageSchema

router = APIRouter(tags=["Autoryzacja"])

# loguje uzytkownika i zwraca token jwt oraz dane profilu
@router.post("/api/login")
def logowanie(request: LoginRequest, db: Session = Depends(get_db)):
    wynik = db.execute(text("""
        SELECT u.id, u.email, u.haslo_hash, u.profil_uzupelniony, r.nazwa AS rola_nazwa
        FROM uzytkownicy u 
        JOIN role r ON u.rola_id = r.id 
        WHERE u.email = :email
    """), {"email": request.email}).fetchone()

    if not wynik or not pwd_context.verify(request.haslo, wynik.haslo_hash):
        raise HTTPException(status_code=401, detail="Nieprawidłowy email lub hasło")

    imie, nazwisko = None, None
    
    if wynik.rola_nazwa == "pacjent":
        profil = db.execute(text("""
            SELECT imie, nazwisko 
            FROM pacjenci 
            WHERE uzytkownik_id = :uid
        """), {"uid": wynik.id}).fetchone()
        
        if profil: 
            imie, nazwisko = profil.imie, profil.nazwisko
            
    elif wynik.rola_nazwa == "lekarz":
        profil = db.execute(text("""
            SELECT imie, nazwisko 
            FROM lekarze 
            WHERE uzytkownik_id = :uid
        """), {"uid": wynik.id}).fetchone()
        
        if profil: 
            imie, nazwisko = profil.imie, profil.nazwisko
            
    elif wynik.rola_nazwa in ["admin", "rejestracja"]:
        profil = db.execute(text("""
            SELECT imie, nazwisko 
            FROM pracownicy 
            WHERE uzytkownik_id = :uid
        """), {"uid": wynik.id}).fetchone()
        
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

# obsluguje logowanie dla dokumentacji swagger ui
@router.post("/api/auth/swagger-token", include_in_schema=False)
def swagger_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    wynik = db.execute(text("""
        SELECT u.id, u.email, u.haslo_hash, r.nazwa AS rola_nazwa 
        FROM uzytkownicy u 
        JOIN role r ON u.rola_id = r.id 
        WHERE u.email = :email
    """), {"email": form_data.username}).fetchone()
    
    if not wynik or not pwd_context.verify(form_data.password, wynik.haslo_hash):
        raise HTTPException(status_code=401, detail="Nieprawidłowy email lub hasło")
        
    return {
        "access_token": stworz_token({"sub": wynik.email, "id": wynik.id, "rola": wynik.rola_nazwa}), 
        "token_type": "bearer"
    }

# rejestruje nowe konto pacjenta w systemie
@router.post("/api/register", status_code=201)
def rejestracja(request: RejestracjaRequest, db: Session = Depends(get_db)):
    if db.execute(text("SELECT id FROM uzytkownicy WHERE email = :email"), {"email": request.email}).fetchone():
        raise HTTPException(status_code=409, detail="Konto z tym adresem email już istnieje")
        
    rola = db.execute(text("SELECT id FROM role WHERE nazwa = 'pacjent'")).fetchone()
    
    if not rola:
        raise HTTPException(status_code=500, detail="Błąd konfiguracji: brak roli 'pacjent' w bazie")
    
    nowy = db.execute(text("""
        INSERT INTO uzytkownicy (email, haslo_hash, rola_id, profil_uzupelniony)
        VALUES (:email, :hash, :rola_id, FALSE) 
        RETURNING id, email
    """), {
        "email": request.email, 
        "hash": pwd_context.hash(request.haslo), 
        "rola_id": rola.id
    }).fetchone()
    
    db.commit()
    return {"status": "sukces", "uzytkownik": {"id": nowy.id, "email": nowy.email}}

# generuje token resetu hasla i wysyla link na email (mailpit)
@router.post("/api/forgot-password", status_code=200)
async def zapomniane_haslo(request: ResetHaslaRequest, db: Session = Depends(get_db)):
    uzytkownik = db.execute(text("""
        SELECT id, email 
        FROM uzytkownicy 
        WHERE email = :email
    """), {"email": request.email}).fetchone()
    
    if not uzytkownik: 
        return {"status": "sukces"}
    
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(minutes=15)
    
    db.execute(text("""
        UPDATE uzytkownicy 
        SET reset_token = :token, reset_token_expires = :expires 
        WHERE id = :id
    """), {
        "token": token, 
        "expires": expires, 
        "id": uzytkownik.id
    })
    
    db.commit()

    link = f"http://localhost:5173/reset-password?token={token}"
    msg = MessageSchema(
        subject="Reset hasła — MediSync",
        recipients=[uzytkownik.email],
        body=f"<h2>Reset hasła MediSync</h2><p>Otrzymaliśmy prośbę o reset hasła dla Twojego konta.</p><p>Kliknij poniższy link aby ustawić nowe hasło:</p><a href='{link}' style='display: inline-block; padding: 12px 24px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;'>Resetuj hasło</a><p>Link jest ważny przez <strong>15 minut</strong>.</p><p>Jeśli nie prosiłeś o reset hasła, zignoruj tę wiadomość.</p><br><p>Zespół MediSync</p>",
        subtype="html"
    )
    await fastmail.send_message(msg)
    
    return {"status": "sukces"}

# ustawia nowe haslo na podstawie waznego tokenu
@router.post("/api/reset-password", status_code=200)
def reset_hasla(request: NoweHasloRequest, db: Session = Depends(get_db)):
    u = db.execute(text("""
        SELECT id 
        FROM uzytkownicy 
        WHERE reset_token = :token AND reset_token_expires > :teraz
    """), {
        "token": request.token, 
        "teraz": datetime.utcnow()
    }).fetchone()
    
    if not u: 
        raise HTTPException(status_code=400, detail="Token jest nieprawidłowy lub wygasł")
        
    if len(request.nowe_haslo) < 12: 
        raise HTTPException(status_code=422, detail="Hasło musi mieć co najmniej 12 znaków")
        
    db.execute(text("""
        UPDATE uzytkownicy 
        SET haslo_hash = :hash, reset_token = NULL, reset_token_expires = NULL 
        WHERE id = :id
    """), {
        "hash": pwd_context.hash(request.nowe_haslo), 
        "id": u.id
    })
    
    db.commit()
    return {"status": "sukces"}

# do uzupelnienia kartoteki po rejestracji - przy pierwsz. logowaniu
@router.post("/api/complete-profile", status_code=200)
def uzupelnij_kartoteke(request: KartotekaRequest, db: Session = Depends(get_db)):
    if db.execute(text("SELECT id FROM pacjenci WHERE pesel = :pesel"), {"pesel": request.pesel}).fetchone():
        raise HTTPException(status_code=409, detail="Pacjent z tym PESELem już istnieje")
    
    adr = db.execute(text("""
        INSERT INTO adresy (miejscowosc, kod_pocztowy, ulica, nr_domu, nr_lokalu) 
        VALUES (:m, :k, :u, :nd, :nl) 
        RETURNING id
    """), {
        "m": request.miejscowosc, 
        "k": request.kod_pocztowy, 
        "u": request.ulica, 
        "nd": request.nr_domu, 
        "nl": request.nr_lokalu
    }).fetchone()
    
    db.execute(text("""
        INSERT INTO pacjenci (uzytkownik_id, adres_id, pesel, imie, nazwisko, telefon) 
        VALUES (:uid, :aid, :p, :i, :n, :t)
    """), {
        "uid": request.uzytkownik_id, 
        "aid": adr.id, 
        "p": request.pesel, 
        "i": request.imie, 
        "n": request.nazwisko, 
        "t": request.telefon
    })
    
    db.execute(text("""
        UPDATE uzytkownicy 
        SET profil_uzupelniony = TRUE 
        WHERE id = :uid
    """), {"uid": request.uzytkownik_id})
    
    db.commit()
    return {"status": "sukces"}