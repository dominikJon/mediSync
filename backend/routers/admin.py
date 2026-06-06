from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db
from models.schemas import DodajLekarzaRequest, DodajPracownika, AktualizacjaUzytkownikaRequest
from dependencies import tylko_admin, pwd_context

router = APIRouter(tags=["Admin"])

# pobiera statystyki na glowny pulpit administratora
@router.get("/api/admin/pulpit")
def pulpit_admina(db: Session = Depends(get_db), payload: dict = Depends(tylko_admin)):
    role_stats = db.execute(text("""
        SELECT r.nazwa, COUNT(u.id) AS liczba 
        FROM role r 
        LEFT JOIN uzytkownicy u ON r.id = u.rola_id 
        GROUP BY r.nazwa 
        ORDER BY r.nazwa
    """)).fetchall()
    
    ostatni = db.execute(text("""
        SELECT u.id, u.email, r.nazwa AS rola, 
               COALESCE(p.imie, l.imie, pr.imie) AS imie, 
               COALESCE(p.nazwisko, l.nazwisko, pr.nazwisko) AS nazwisko 
        FROM uzytkownicy u 
        JOIN role r ON u.rola_id = r.id 
        LEFT JOIN pacjenci p ON u.id = p.uzytkownik_id 
        LEFT JOIN lekarze l ON u.id = l.uzytkownik_id 
        LEFT JOIN pracownicy pr ON u.id = pr.uzytkownik_id 
        ORDER BY u.id DESC 
        LIMIT 5
    """)).fetchall()
    
    gabinety = db.execute(text("""
        SELECT 
            COUNT(*) FILTER (WHERE status = 'Dostępny') AS dostepne, 
            COUNT(*) FILTER (WHERE status = 'Niedostępny') AS niedostepne 
        FROM gabinety
    """)).fetchone()
    
    return {
        "uzytkownicy": {r.nazwa: r.liczba for r in role_stats},
        "ostatni_uzytkownicy": [{"id": u.id, "email": u.email, "rola": u.rola, "imie": u.imie, "nazwisko": u.nazwisko} for u in ostatni],
        "gabinety": {"dostepne": gabinety.dostepne, "niedostepne": gabinety.niedostepne}
    }

# zwraca liste wszystkich uzytkownikow w systemie
@router.get("/api/admin/users")
def lista_uzytkownikow(db: Session = Depends(get_db), payload: dict = Depends(tylko_admin)):
    wyniki = db.execute(text("""
        SELECT u.id, u.email, u.profil_uzupelniony, r.nazwa AS rola, 
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
                "id": w.id, "email": w.email, "rola": w.rola, 
                "profil_uzupelniony": w.profil_uzupelniony, 
                "imie": w.imie, "nazwisko": w.nazwisko
            } for w in wyniki
        ]
    }

# dodaje nowe konto lekarza wraz z profilem
@router.post("/api/admin/add-doctor", status_code=201)
def dodaj_lekarza(request: DodajLekarzaRequest, db: Session = Depends(get_db), payload: dict = Depends(tylko_admin)):
    try:
        if db.execute(text("SELECT id FROM uzytkownicy WHERE email = :email"), {"email": request.email}).fetchone(): 
            raise HTTPException(status_code=409, detail="Email już istnieje")
            
        if db.execute(text("SELECT id FROM lekarze WHERE npwz = :npwz"), {"npwz": request.npwz}).fetchone(): 
            raise HTTPException(status_code=409, detail="Lekarz z tym NPWZ już istnieje")
            
        if not request.brak_peselu and request.pesel:
            if db.execute(text("SELECT id FROM lekarze WHERE pesel = :pesel"), {"pesel": request.pesel}).fetchone(): 
                raise HTTPException(status_code=409, detail="Lekarz z tym PESELem już istnieje")
                
        if not db.execute(text("SELECT id FROM placowki WHERE id = :id"), {"id": request.placowka_id}).fetchone(): 
            raise HTTPException(status_code=404, detail="Placówka nie istnieje")
            
        for spec_id in request.specjalizacje_ids:
            if not db.execute(text("SELECT id FROM specjalizacje WHERE id = :id"), {"id": spec_id}).fetchone(): 
                raise HTTPException(status_code=404, detail=f"Specjalizacja o id {spec_id} nie istnieje")
        
        rola = db.execute(text("SELECT id FROM role WHERE nazwa = 'lekarz'")).fetchone()
        if not rola: 
            raise HTTPException(status_code=500, detail="Brak roli 'lekarz' w bazie")
        
        nowy_user = db.execute(text("""
            INSERT INTO uzytkownicy (email, haslo_hash, rola_id, profil_uzupelniony) 
            VALUES (:email, :haslo_hash, :rola_id, TRUE) 
            RETURNING id
        """), {
            "email": request.email, 
            "haslo_hash": pwd_context.hash(request.haslo), 
            "rola_id": rola.id
        }).fetchone()
        
        nowy_lek = db.execute(text("""
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
            "telefon": request.telefon
        }).fetchone()
        
        for spec_id in request.specjalizacje_ids:
            db.execute(text("""
                INSERT INTO lekarz_specjalizacja (lekarz_id, specjalizacja_id) 
                VALUES (:lekarz_id, :specjalizacja_id)
            """), {
                "lekarz_id": nowy_lek.id, 
                "specjalizacja_id": spec_id
            })
            
        db.commit()
        return {"status": "sukces", "lekarz_id": nowy_lek.id, "uzytkownik_id": nowy_user.id}
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Błąd podczas dodawania lekarza: {str(e)}")

# dodaje nowe konto pracownika administracji lub recepcji
@router.post("/api/admin/add-staff", status_code=201)
def dodaj_pracownika(request: DodajPracownika, db: Session = Depends(get_db), payload: dict = Depends(tylko_admin)):
    try:
        if db.execute(text("SELECT id FROM uzytkownicy WHERE email = :email"), {"email": request.email}).fetchone(): 
            raise HTTPException(status_code=409, detail="Email już istnieje")
            
        if not request.brak_peselu and request.pesel:
            if db.execute(text("SELECT id FROM pracownicy WHERE pesel = :pesel"), {"pesel": request.pesel}).fetchone(): 
                raise HTTPException(status_code=409, detail="Pracownik z tym PESELem już istnieje")
                
        rola = db.execute(text("SELECT id FROM role WHERE nazwa = :nazwa"), {"nazwa": request.rola}).fetchone()
        if not rola: 
            raise HTTPException(status_code=500, detail=f"Brak roli '{request.rola}' w bazie")
        
        nowy_user = db.execute(text("""
            INSERT INTO uzytkownicy (email, haslo_hash, rola_id, profil_uzupelniony) 
            VALUES (:email, :haslo_hash, :rola_id, TRUE) 
            RETURNING id
        """), {
            "email": request.email, 
            "haslo_hash": pwd_context.hash(request.haslo), 
            "rola_id": rola.id
        }).fetchone()
        
        nowy_pracownik = db.execute(text("""
            INSERT INTO pracownicy (uzytkownik_id, imie, nazwisko, pesel, telefon) 
            VALUES (:uzytkownik_id, :imie, :nazwisko, :pesel, :telefon) 
            RETURNING id
        """), {
            "uzytkownik_id": nowy_user.id, 
            "imie": request.imie, 
            "nazwisko": request.nazwisko, 
            "pesel": request.pesel, 
            "telefon": request.telefon
        }).fetchone()
        
        db.commit()
        return {"status": "sukces", "pracownik_id": nowy_pracownik.id, "uzytkownik_id": nowy_user.id}
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Błąd podczas dodawania pracownika: {str(e)}")

# pobiera liste dostepnych placowek medycznych
@router.get("/api/admin/placowki")
def lista_placowek(db: Session = Depends(get_db), payload: dict = Depends(tylko_admin)):
    wyniki = db.execute(text("SELECT id, nazwa FROM placowki ORDER BY nazwa")).fetchall()
    return {"placowki": [{"id": w.id, "nazwa": w.nazwa} for w in wyniki]}

# pobiera liste dostepnych specjalizacji lekarskich
@router.get("/api/admin/specjalizacje")
def lista_specjalizacji(db: Session = Depends(get_db), payload: dict = Depends(tylko_admin)):
    wyniki = db.execute(text("SELECT id, nazwa FROM specjalizacje ORDER BY nazwa")).fetchall()
    return {"specjalizacje": [{"id": w.id, "nazwa": w.nazwa} for w in wyniki]}

# pobiera szczegolowe dane wybranego uzytkownika
@router.get("/api/admin/user/{user_id}")
def pobierz_uzytkownika(user_id: int, db: Session = Depends(get_db), payload: dict = Depends(tylko_admin)):
    uzytkownik = db.execute(text("""
        SELECT u.id, u.email, u.profil_uzupelniony, r.nazwa AS rola 
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
        "profil": None
    }
    
    if uzytkownik.rola == "pacjent":
        profil = db.execute(text("""
            SELECT p.imie, p.nazwisko, p.pesel, p.telefon, a.miejscowosc, a.kod_pocztowy, a.ulica, a.nr_domu, a.nr_lokalu 
            FROM pacjenci p 
            LEFT JOIN adresy a ON p.adres_id = a.id 
            WHERE p.uzytkownik_id = :id
        """), {"id": user_id}).fetchone()
        
        if profil: 
            dane["profil"] = dict(profil._mapping)
            
    elif uzytkownik.rola == "lekarz":
        profil = db.execute(text("""
            SELECT l.imie, l.nazwisko, l.pesel, l.npwz, l.status_npwz, l.waznosc_oc, l.placowka_id, l.telefon, p.nazwa AS placowka_nazwa 
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
            dane["profil"] = dict(profil._mapping)
            dane["profil"]["specjalizacje"] = [{"id": s.id, "nazwa": s.nazwa} for s in specjalizacje]
            
    elif uzytkownik.rola in ["admin", "rejestracja"]:
        profil = db.execute(text("""
            SELECT imie, nazwisko, telefon, pesel 
            FROM pracownicy 
            WHERE uzytkownik_id = :id
        """), {"id": user_id}).fetchone()
        
        if profil: 
            dane["profil"] = dict(profil._mapping)
            
    return dane

# aktualizuje dane i role wybranego uzytkownika
@router.put("/api/admin/user/{user_id}", status_code=200)
def aktualizuj_uzytkownika(user_id: int, request: AktualizacjaUzytkownikaRequest, db: Session = Depends(get_db), payload: dict = Depends(tylko_admin)):
    uzytkownik = db.execute(text("""
        SELECT u.id, r.nazwa AS rola 
        FROM uzytkownicy u 
        JOIN role r ON u.rola_id = r.id 
        WHERE u.id = :id
    """), {"id": user_id}).fetchone()
    
    if not uzytkownik: 
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")

    if request.rola and request.rola != uzytkownik.rola:
        nowa_rola = db.execute(text("SELECT id FROM role WHERE nazwa = :nazwa"), {"nazwa": request.rola}).fetchone()
        if not nowa_rola: 
            raise HTTPException(status_code=404, detail="Rola nie istnieje")
        db.execute(text("UPDATE uzytkownicy SET rola_id = :rola_id WHERE id = :id"), {"rola_id": nowa_rola.id, "id": user_id})

    rola = request.rola or uzytkownik.rola

    if rola == "pacjent":
        pacjent = db.execute(text("SELECT id, adres_id FROM pacjenci WHERE uzytkownik_id = :id"), {"id": user_id}).fetchone()
        if pacjent:
            db.execute(text("""
                UPDATE pacjenci 
                SET imie = COALESCE(:imie, imie), 
                    nazwisko = COALESCE(:nazwisko, nazwisko), 
                    telefon = COALESCE(:telefon, telefon) 
                WHERE uzytkownik_id = :id
            """), {
                "imie": request.imie, 
                "nazwisko": request.nazwisko, 
                "telefon": request.telefon, 
                "id": user_id
            })
            
            if pacjent.adres_id and any([request.miejscowosc, request.kod_pocztowy, request.ulica, request.nr_domu, request.nr_lokalu]):
                db.execute(text("""
                    UPDATE adresy 
                    SET miejscowosc = COALESCE(:miejscowosc, miejscowosc), 
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
                    "adres_id": pacjent.adres_id
                })

    elif rola == "lekarz":
        lekarz = db.execute(text("SELECT id FROM lekarze WHERE uzytkownik_id = :id"), {"id": user_id}).fetchone()
        if lekarz:
            db.execute(text("""
                UPDATE lekarze 
                SET imie = COALESCE(:imie, imie), 
                    nazwisko = COALESCE(:nazwisko, nazwisko), 
                    telefon = COALESCE(:telefon, telefon), 
                    status_npwz = COALESCE(:status_npwz, status_npwz), 
                    waznosc_oc = COALESCE(CAST(:waznosc_oc AS DATE), waznosc_oc), 
                    placowka_id = COALESCE(:placowka_id, placowka_id) 
                WHERE id = :id
            """), {
                "imie": request.imie, 
                "nazwisko": request.nazwisko, 
                "telefon": request.telefon, 
                "status_npwz": request.status_npwz, 
                "waznosc_oc": request.waznosc_oc, 
                "placowka_id": request.placowka_id, 
                "id": lekarz.id
            })
            
            if request.specjalizacje_ids is not None:
                db.execute(text("DELETE FROM lekarz_specjalizacja WHERE lekarz_id = :id"), {"id": lekarz.id})
                for spec_id in request.specjalizacje_ids:
                    db.execute(text("""
                        INSERT INTO lekarz_specjalizacja (lekarz_id, specjalizacja_id) 
                        VALUES (:lekarz_id, :spec_id) 
                        ON CONFLICT DO NOTHING
                    """), {
                        "lekarz_id": lekarz.id, 
                        "spec_id": spec_id
                    })

    elif rola in ["admin", "rejestracja"]:
        db.execute(text("""
            UPDATE pracownicy 
            SET imie = COALESCE(:imie, imie), 
                nazwisko = COALESCE(:nazwisko, nazwisko), 
                telefon = COALESCE(:telefon, telefon) 
            WHERE uzytkownik_id = :id
        """), {
            "imie": request.imie, 
            "nazwisko": request.nazwisko, 
            "telefon": request.telefon, 
            "id": user_id
        })

    db.commit()
    return {"status": "sukces"}