from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from datetime import date, datetime, timezone, timedelta
from typing import Optional
from fastapi_mail import MessageSchema

from database import get_db
from models.schemas import RezerwacjaRequest
from dependencies import kazdy_zalogowany, tylko_admin_lub_rejestracja, fastmail

router = APIRouter(tags=["Wizyty i Rezerwacje"])

# pobiera liste wszystkich specjalizacji medycznych
@router.get("/api/specjalizacje/lista")
def lista_specjalizacji(db: Session = Depends(get_db), payload: dict = Depends(kazdy_zalogowany)):
    wyniki = db.execute(text("""
        SELECT id, nazwa 
        FROM specjalizacje 
        ORDER BY nazwa
    """)).fetchall()
    
    return {
        "specjalizacje": [{"id": w.id, "nazwa": w.nazwa} for w in wyniki]
    }

# pobiera liste lekarzy z opcjonalnym filtrowaniem po specjalizacji
@router.get("/api/lekarze/lista")
def lista_lekarzy(specjalizacja_id: Optional[int] = None, db: Session = Depends(get_db), payload: dict = Depends(kazdy_zalogowany)):
    z = """
        SELECT l.id, l.imie, l.nazwisko, array_remove(array_agg(s.nazwa), NULL) AS specjalizacje 
        FROM lekarze l 
        LEFT JOIN lekarz_specjalizacja ls ON l.id = ls.lekarz_id 
        LEFT JOIN specjalizacje s ON ls.specjalizacja_id = s.id
    """
    p = {}
    
    if specjalizacja_id:
        z += " WHERE l.id IN (SELECT lekarz_id FROM lekarz_specjalizacja WHERE specjalizacja_id = :spec_id)"
        p["spec_id"] = specjalizacja_id
        
    z += " GROUP BY l.id, l.imie, l.nazwisko ORDER BY l.nazwisko, l.imie"
    
    wyniki = db.execute(text(z), p).fetchall()
    
    return {
        "lekarze": [
            {
                "id": w.id, 
                "imie": w.imie, 
                "nazwisko": w.nazwisko, 
                "specjalizacje": w.specjalizacje, 
                "placowka": "Przychodnia MediSync"
            } for w in wyniki
        ]
    }

# pobiera dostepne terminy wizyt dla wybranego lekarza i dnia
@router.get("/api/wizyty/wolne-sloty")
def wolne_sloty_lekarza(lekarz_id: int, data: date, db: Session = Depends(get_db), payload: dict = Depends(kazdy_zalogowany)):
    if data < date.today(): 
        raise HTTPException(status_code=400, detail="Nie można wyszukiwać terminów w przeszłości.")
        
    wyniki = db.execute(text("""
        SELECT gp.id, gp.termin_od, gp.termin_do, g.numer AS gabinet_numer, 
               (SELECT c.cena 
                FROM cennik c 
                JOIN lekarz_specjalizacja ls ON ls.lekarz_id = gp.lekarz_id 
                WHERE c.specjalizacja_id = ls.specjalizacja_id 
                  AND (c.data_do IS NULL OR c.data_do > NOW()) 
                ORDER BY c.id LIMIT 1) AS cena 
        FROM grafiki_pracy gp 
        JOIN gabinety g ON gp.gabinet_id = g.id 
        LEFT JOIN wizyty w ON gp.id = w.grafik_id AND w.status = 'Zaplanowana' 
        WHERE gp.lekarz_id = :lekarz_id 
          AND DATE(gp.termin_od) = :data 
          AND w.id IS NULL 
          AND gp.termin_od > NOW()
          AND g.status = 'Dostępny' 
        ORDER BY gp.termin_od
    """), {"lekarz_id": lekarz_id, "data": data}).fetchall()
    
    return {
        "sloty": [
            {
                "id": w.id, 
                "termin_od": w.termin_od.isoformat(), 
                "termin_do": w.termin_do.isoformat(), 
                "gabinet_numer": w.gabinet_numer, 
                "cena": float(w.cena) if w.cena else None
            } for w in wyniki
        ]
    }

# wyszukuje pacjentow na potrzeby rejestracji
@router.get("/api/pacjenci/szukaj")
def szukaj_pacjentow(q: str = Query(..., min_length=2), db: Session = Depends(get_db), payload: dict = Depends(tylko_admin_lub_rejestracja)):
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
            } for w in wyniki
        ]
    }

# rezerwuje wybrany termin wizyty dla pacjenta
@router.post("/api/wizyty")
def zarezerwuj_wizyte(request: RezerwacjaRequest, db: Session = Depends(get_db), payload: dict = Depends(kazdy_zalogowany)):
    rola = payload.get("rola")
    
    if rola == "pacjent":
        pacjent = db.execute(text("""
            SELECT id 
            FROM pacjenci 
            WHERE uzytkownik_id = :uid
        """), {"uid": payload.get("id")}).fetchone()
        
        if not pacjent: 
            raise HTTPException(status_code=404, detail="Nie znaleziono profilu pacjenta.")
        pacjent_id = pacjent.id
        
    elif rola in ["admin", "rejestracja"]:
        if not request.pacjent_id: 
            raise HTTPException(status_code=422, detail="Rejestracja musi podać pacjent_id.")
        pacjent_id = request.pacjent_id
        
    else: 
        raise HTTPException(status_code=403, detail="Brak uprawnień do rezerwacji.")

    try:
        slot = db.execute(text("""
            SELECT gp.id, gp.termin_od, l.imie, l.nazwisko, g.numer as gabinet 
            FROM grafiki_pracy gp 
            JOIN lekarze l ON gp.lekarz_id = l.id 
            JOIN gabinety g ON gp.gabinet_id = g.id 
            WHERE gp.id = :grafik_id 
            FOR UPDATE NOWAIT
        """), {"grafik_id": request.grafik_id}).fetchone()
        
        if not slot: 
            raise HTTPException(status_code=404, detail="Nie znaleziono slotu.")
            
        if db.execute(text("""
            SELECT id 
            FROM wizyty 
            WHERE grafik_id = :grafik_id 
              AND status = 'Zaplanowana'
        """), {"grafik_id": request.grafik_id}).fetchone(): 
            raise HTTPException(status_code=409, detail="Ten slot jest już zajęty.")
        
        cennik = db.execute(text("""
            SELECT c.id, c.cena 
            FROM cennik c 
            JOIN lekarz_specjalizacja ls ON ls.specjalizacja_id = c.specjalizacja_id 
            WHERE ls.lekarz_id = (SELECT lekarz_id FROM grafiki_pracy WHERE id = :grafik_id) 
              AND (c.data_do IS NULL OR c.data_do > NOW()) 
            ORDER BY c.id LIMIT 1
        """), {"grafik_id": request.grafik_id}).fetchone()
        
        if not cennik: 
            cennik = db.execute(text("""
                SELECT id, cena 
                FROM cennik 
                WHERE specjalizacja_id IS NULL 
                  AND (data_do IS NULL OR data_do > NOW()) 
                LIMIT 1
            """)).fetchone()
            
        if not cennik: 
            raise HTTPException(status_code=500, detail="Błąd systemu: Brak cennika dla tej specjalizacji.")

        n_id = db.execute(text("""
            INSERT INTO wizyty (pacjent_id, grafik_id, cennik_id, status) 
            VALUES (:pacjent_id, :grafik_id, :cennik_id, 'Zaplanowana') 
            RETURNING id
        """), {
            "pacjent_id": pacjent_id, 
            "grafik_id": request.grafik_id, 
            "cennik_id": cennik.id
        }).fetchone()[0]
        
        db.commit()
        
        return {
            "status": "sukces", 
            "wizyta_id": n_id, 
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

# pobiera liste wizyt zalogowanego pacjenta
@router.get("/api/wizyty/moje")
def moje_wizyty(db: Session = Depends(get_db), payload: dict = Depends(kazdy_zalogowany)):
    if payload.get("rola") != "pacjent": 
        raise HTTPException(status_code=403, detail="Tylko pacjent może przeglądać listę wizyt.")
        
    pacjent = db.execute(text("""
        SELECT id 
        FROM pacjenci 
        WHERE uzytkownik_id = :uid
    """), {"uid": payload.get("id")}).fetchone()
    
    if not pacjent: 
        raise HTTPException(status_code=404, detail="Nie znaleziono profilu pacjenta.")
    
    wyniki = db.execute(text("""
        SELECT w.id, w.status, gp.termin_od, gp.termin_do, 
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
    """), {"pacjent_id": pacjent.id}).fetchall()
    
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

# pobiera pelny harmonogram wizyt na dany dzien dla recepcji
@router.get("/api/reception/wizyty")
def lista_wizyt_recepcji(data: Optional[date] = None, db: Session = Depends(get_db), payload: dict = Depends(tylko_admin_lub_rejestracja)):
    if not data: 
        data = date.today()
        
    wizyty = db.execute(text("""
        SELECT w.id, w.status, gp.termin_od, gp.termin_do, 
               p.imie AS pacjent_imie, p.nazwisko AS pacjent_nazwisko, p.telefon AS pacjent_telefon, 
               l.imie AS lekarz_imie, l.nazwisko AS lekarz_nazwisko, 
               g.numer AS gabinet 
        FROM wizyty w 
        JOIN grafiki_pracy gp ON w.grafik_id = gp.id 
        JOIN pacjenci p ON w.pacjent_id = p.id 
        JOIN lekarze l ON gp.lekarz_id = l.id 
        JOIN gabinety g ON gp.gabinet_id = g.id 
        WHERE DATE(gp.termin_od) = :data 
        ORDER BY gp.termin_od ASC
    """), {"data": data}).fetchall()
    
    return {
        "wizyty": [
            {
                "id": w.id, 
                "status": w.status, 
                "termin_od": w.termin_od.isoformat(), 
                "termin_do": w.termin_do.isoformat(), 
                "pacjent": f"{w.pacjent_imie} {w.pacjent_nazwisko}", 
                "pacjent_telefon": w.pacjent_telefon, 
                "lekarz": f"dr {w.lekarz_imie} {w.lekarz_nazwisko}", 
                "gabinet": w.gabinet
            } for w in wizyty
        ]
    }

# anuluje wizyte i wysyla powiadomienia email
@router.delete("/api/wizyty/{wizyta_id}")
async def odwolaj_wizyte(wizyta_id: int, db: Session = Depends(get_db), payload: dict = Depends(kazdy_zalogowany)):
    wizyta = db.execute(text("""
        SELECT w.id, w.pacjent_id, w.status, gp.termin_od, gp.lekarz_id, 
               l.imie AS lekarz_imie, l.nazwisko AS lekarz_nazwisko, ul.email AS lekarz_email, 
               p.imie AS pacjent_imie, p.nazwisko AS pacjent_nazwisko, up.email AS pacjent_email, 
               g.numer AS gabinet_numer 
        FROM wizyty w 
        JOIN grafiki_pracy gp ON w.grafik_id = gp.id 
        JOIN lekarze l ON gp.lekarz_id = l.id 
        JOIN uzytkownicy ul ON l.uzytkownik_id = ul.id 
        JOIN pacjenci p ON w.pacjent_id = p.id 
        JOIN uzytkownicy up ON p.uzytkownik_id = up.id 
        JOIN gabinety g ON gp.gabinet_id = g.id 
        WHERE w.id = :wizyta_id
    """), {"wizyta_id": wizyta_id}).fetchone()
    
    if not wizyta: 
        raise HTTPException(status_code=404, detail="Nie znaleziono wizyty.")
    if wizyta.status == "Odwołana": 
        raise HTTPException(status_code=400, detail="Wizyta jest już odwołana.")
    if wizyta.status == "Zakończona": 
        raise HTTPException(status_code=400, detail="Nie można odwołać zakończonej wizyty.")

    rola = payload.get("rola")
    now_time = datetime.now(timezone.utc) if wizyta.termin_od.tzinfo else datetime.now()

    if rola == "pacjent":
        pacjent = db.execute(text("""
            SELECT id 
            FROM pacjenci 
            WHERE uzytkownik_id = :uid
        """), {"uid": payload.get("id")}).fetchone()
        
        if not pacjent or wizyta.pacjent_id != pacjent.id: 
            raise HTTPException(status_code=403, detail="Nie masz uprawnień do odwołania tej wizyty.")
        if wizyta.termin_od <= now_time + timedelta(hours=24): 
            raise HTTPException(status_code=409, detail="Odwołanie możliwe tylko 24h przed terminem.")
            
    elif rola == "lekarz":
        lekarz = db.execute(text("""
            SELECT id 
            FROM lekarze 
            WHERE uzytkownik_id = :uid
        """), {"uid": payload.get("id")}).fetchone()
        
        if not lekarz or wizyta.lekarz_id != lekarz.id: 
            raise HTTPException(status_code=403, detail="Nie masz uprawnień do odwołania tej wizyty.")
        if wizyta.termin_od <= now_time + timedelta(hours=24): 
            raise HTTPException(status_code=409, detail="Odwołanie możliwe tylko 24h przed terminem.")
            
    elif rola not in ["admin", "rejestracja"]:
        raise HTTPException(status_code=403, detail="Brak uprawnień.")

    try:
        db.execute(text("""
            UPDATE wizyty 
            SET status = 'Odwołana' 
            WHERE id = :id
        """), {"id": wizyta_id})
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Błąd podczas odwoływania wizyty: {str(e)}")

    termin = wizyta.termin_od.strftime("%d.%m.%Y o %H:%M")
    
    recepcjonisci = db.execute(text("""
        SELECT u.email 
        FROM uzytkownicy u 
        JOIN role r ON u.rola_id = r.id 
        WHERE r.nazwa = 'rejestracja'
    """)).fetchall()
    
    emaile_recepcji = [r.email for r in recepcjonisci]

    def tresc_dla_lekarza(kto_odwolal: str) -> str:
        return f"<h2>Odwołanie wizyty — MediSync</h2><p>Wizyta została odwołana przez <strong>{kto_odwolal}</strong>.</p><table style='border-collapse: collapse; margin: 16px 0;'><tr><td style='padding: 8px 16px 8px 0; color: #64748b; font-weight: 600;'>Pacjent:</td><td>{wizyta.pacjent_imie} {wizyta.pacjent_nazwisko}</td></tr><tr><td style='padding: 8px 16px 8px 0; color: #64748b; font-weight: 600;'>Termin:</td><td><strong>{termin}</strong></td></tr><tr><td style='padding: 8px 16px 8px 0; color: #64748b; font-weight: 600;'>Gabinet:</td><td>{wizyta.gabinet_numer}</td></tr></table><p>Zespół MediSync</p>"

    def tresc_dla_pacjenta(kto_odwolal: str) -> str:
        return f"<h2>Odwołanie wizyty — MediSync</h2><p>Drogi/a {wizyta.pacjent_imie} {wizyta.pacjent_nazwisko},</p><p>Twoja wizyta została odwołana przez <strong>{kto_odwolal}</strong>.</p><table style='border-collapse: collapse; margin: 16px 0;'><tr><td style='padding: 8px 16px 8px 0; color: #64748b; font-weight: 600;'>Lekarz:</td><td>dr {wizyta.lekarz_imie} {wizyta.lekarz_nazwisko}</td></tr><tr><td style='padding: 8px 16px 8px 0; color: #64748b; font-weight: 600;'>Termin:</td><td><strong>{termin}</strong></td></tr><tr><td style='padding: 8px 16px 8px 0; color: #64748b; font-weight: 600;'>Gabinet:</td><td>{wizyta.gabinet_numer}</td></tr></table><a href='http://localhost:5173/schedule' style='display: inline-block; padding: 12px 24px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;'>Zarezerwuj nowy termin</a><br><br><p>Zespół MediSync</p>"

    def tresc_dla_recepcji(kto_odwolal: str) -> str:
        return f"<h2>Odwołanie wizyty — MediSync</h2><p>Wizyta została odwołana przez <strong>{kto_odwolal}</strong>.</p><table style='border-collapse: collapse; margin: 16px 0;'><tr><td style='padding: 8px 16px 8px 0; color: #64748b; font-weight: 600;'>Pacjent:</td><td>{wizyta.pacjent_imie} {wizyta.pacjent_nazwisko}</td></tr><tr><td style='padding: 8px 16px 8px 0; color: #64748b; font-weight: 600;'>Lekarz:</td><td>dr {wizyta.lekarz_imie} {wizyta.lekarz_nazwisko}</td></tr><tr><td style='padding: 8px 16px 8px 0; color: #64748b; font-weight: 600;'>Termin:</td><td><strong>{termin}</strong></td></tr><tr><td style='padding: 8px 16px 8px 0; color: #64748b; font-weight: 600;'>Gabinet:</td><td>{wizyta.gabinet_numer}</td></tr></table><p>Zespół MediSync</p>"

    if rola == "pacjent":
        await fastmail.send_message(MessageSchema(subject="Odwołanie wizyty — MediSync", recipients=[wizyta.lekarz_email], body=tresc_dla_lekarza("pacjenta"), subtype="html"))
        if emaile_recepcji: 
            await fastmail.send_message(MessageSchema(subject="Odwołanie wizyty — MediSync", recipients=emaile_recepcji, body=tresc_dla_recepcji("pacjenta"), subtype="html"))
            
    elif rola == "lekarz":
        await fastmail.send_message(MessageSchema(subject="Odwołanie wizyty — MediSync", recipients=[wizyta.pacjent_email], body=tresc_dla_pacjenta("lekarza"), subtype="html"))
        if emaile_recepcji: 
            await fastmail.send_message(MessageSchema(subject="Odwołanie wizyty — MediSync", recipients=emaile_recepcji, body=tresc_dla_recepcji("lekarza"), subtype="html"))
            
    elif rola in ["admin", "rejestracja"]:
        await fastmail.send_message(MessageSchema(subject="Odwołanie wizyty — MediSync", recipients=[wizyta.pacjent_email], body=tresc_dla_pacjenta("recepcji"), subtype="html"))
        await fastmail.send_message(MessageSchema(subject="Odwołanie wizyty — MediSync", recipients=[wizyta.lekarz_email], body=tresc_dla_lekarza("recepcji"), subtype="html"))

    return {"status": "sukces", "wiadomosc": "Wizyta została odwołana."}