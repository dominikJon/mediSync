from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date
import json

from database import get_db
from models.schemas import DokumentacjaRequest
from dependencies import tylko_lekarz

router = APIRouter(tags=["Lekarz"])

# pobiera kluczowe informacje na glowny ekran pulpitu lekarza
@router.get("/api/lekarz/pulpit")
def pulpit_lekarza(db: Session = Depends(get_db), payload: dict = Depends(tylko_lekarz)):
    lekarz = db.execute(text("SELECT id FROM lekarze WHERE uzytkownik_id = :uid"), {"uid": payload["id"]}).fetchone()
    if not lekarz: 
        raise HTTPException(status_code=404, detail="Nie znaleziono profilu lekarza")

    wizyty_dzis = db.execute(text("""
        SELECT w.id, w.status, gp.termin_od, gp.termin_do, 
               p.imie AS pacjent_imie, p.nazwisko AS pacjent_nazwisko, 
               g.numer AS gabinet 
        FROM wizyty w 
        JOIN grafiki_pracy gp ON w.grafik_id = gp.id 
        JOIN pacjenci p ON w.pacjent_id = p.id 
        JOIN gabinety g ON gp.gabinet_id = g.id 
        WHERE gp.lekarz_id = :lid 
          AND DATE(gp.termin_od) = CURRENT_DATE 
          AND w.status = 'Zaplanowana' 
        ORDER BY gp.termin_od ASC
    """), {"lid": lekarz.id}).fetchall()
    
    stats_tydzien = db.execute(text("""
        SELECT 
            COUNT(*) FILTER (WHERE w.status = 'Zaplanowana') AS zaplanowane, 
            COUNT(*) FILTER (WHERE w.status = 'Zakończona') AS zakonczone, 
            COUNT(*) FILTER (WHERE w.status = 'Odwołana') AS odwolane 
        FROM wizyty w 
        JOIN grafiki_pracy gp ON w.grafik_id = gp.id 
        WHERE gp.lekarz_id = :lid 
          AND gp.termin_od >= DATE_TRUNC('week', NOW()) 
          AND gp.termin_od < DATE_TRUNC('week', NOW()) + INTERVAL '7 days'
    """), {"lid": lekarz.id}).fetchone()
    
    stats_total = db.execute(text("""
        SELECT 
            COUNT(*) FILTER (WHERE w.status = 'Zakończona') AS wszystkie_zakonczone, 
            COUNT(DISTINCT w.pacjent_id) AS unikalni_pacjenci 
        FROM wizyty w 
        JOIN grafiki_pracy gp ON w.grafik_id = gp.id 
        WHERE gp.lekarz_id = :lid
    """), {"lid": lekarz.id}).fetchone()
    
    top_icd = db.execute(text("""
        SELECT dm.kod_icd10, icd.nazwa, COUNT(*) AS liczba 
        FROM dokumentacja_medyczna dm 
        JOIN wizyty w ON dm.wizyta_id = w.id 
        JOIN grafiki_pracy gp ON w.grafik_id = gp.id 
        JOIN slownik_icd10 icd ON dm.kod_icd10 = icd.kod 
        WHERE gp.lekarz_id = :lid 
          AND dm.kod_icd10 IS NOT NULL 
        GROUP BY dm.kod_icd10, icd.nazwa 
        ORDER BY liczba DESC 
        LIMIT 1
    """), {"lid": lekarz.id}).fetchone()

    return {
        "wizyty_dzis": [
            {
                "id": w.id, 
                "status": w.status, 
                "termin_od": w.termin_od.isoformat(), 
                "termin_do": w.termin_do.isoformat(), 
                "pacjent": f"{w.pacjent_imie} {w.pacjent_nazwisko}", 
                "gabinet": w.gabinet
            } for w in wizyty_dzis
        ], 
        "statystyki": {
            "tydzien": {
                "zaplanowane": stats_tydzien.zaplanowane, 
                "zakonczone": stats_tydzien.zakonczone, 
                "odwolane": stats_tydzien.odwolane
            }, 
            "total": {
                "zakonczone": stats_total.wszystkie_zakonczone, 
                "unikalni_pacjenci": stats_total.unikalni_pacjenci, 
                "top_icd": {
                    "kod": top_icd.kod_icd10, 
                    "nazwa": top_icd.nazwa, 
                    "liczba": top_icd.liczba
                } if top_icd else None
            }
        }
    }

# pobiera zblizajace sie wizyty na dany dzien w kalendarzu
@router.get("/api/lekarz/wizyty")
def wizyty_lekarza(data: date = Query(...), db: Session = Depends(get_db), payload: dict = Depends(tylko_lekarz)):
    lekarz = db.execute(text("SELECT id FROM lekarze WHERE uzytkownik_id = :uid"), {"uid": payload["id"]}).fetchone()
    if not lekarz: 
        raise HTTPException(status_code=404, detail="Nie znaleziono profilu lekarza")

    # trigger do auto-zamkniecia przeterminowanych wizyt (>24h bez EDM)
    db.execute(text("""
        UPDATE wizyty SET status = 'Nieobecność'
        WHERE status = 'Zaplanowana'
        AND grafik_id IN (
            SELECT id FROM grafiki_pracy
            WHERE termin_od < NOW() - INTERVAL '24 hours'
        )
    """))
    db.commit()
        
    wizyty = db.execute(text("""
        SELECT w.id, w.status, gp.termin_od, gp.termin_do, 
               p.imie AS pacjent_imie, p.nazwisko AS pacjent_nazwisko, p.pesel, p.telefon, 
               g.numer AS gabinet, c.nazwa_uslugi, c.cena 
        FROM wizyty w 
        JOIN grafiki_pracy gp ON w.grafik_id = gp.id 
        JOIN pacjenci p ON w.pacjent_id = p.id 
        JOIN gabinety g ON gp.gabinet_id = g.id 
        JOIN cennik c ON w.cennik_id = c.id 
        WHERE gp.lekarz_id = :lid 
          AND DATE(gp.termin_od) = :data 
          AND w.status != 'Odwołana' 
        ORDER BY gp.termin_od ASC
    """), {"lid": lekarz.id, "data": data}).fetchall()
    
    return {
        "wizyty": [
            {
                "id": w.id, 
                "status": w.status, 
                "termin_od": w.termin_od.isoformat(), 
                "termin_do": w.termin_do.isoformat(), 
                "pacjent": f"{w.pacjent_imie} {w.pacjent_nazwisko}", 
                "pacjent_pesel": w.pesel, 
                "pacjent_telefon": w.telefon, 
                "gabinet": w.gabinet, 
                "nazwa_uslugi": w.nazwa_uslugi, 
                "cena": str(w.cena)
            } for w in wizyty
        ]
    }

# zwraca chronologiczna liste zakonczonych wizyt
@router.get("/api/lekarz/historia")
def historia_lekarza(db: Session = Depends(get_db), payload: dict = Depends(tylko_lekarz)):
    lekarz = db.execute(text("SELECT id FROM lekarze WHERE uzytkownik_id = :uid"), {"uid": payload["id"]}).fetchone()
    if not lekarz: 
        raise HTTPException(status_code=404, detail="Nie znaleziono profilu lekarza")
        
    wizyty = db.execute(text("""
        SELECT w.id, w.status, gp.termin_od, gp.termin_do, 
               p.imie AS pacjent_imie, p.nazwisko AS pacjent_nazwisko, p.pesel, 
               g.numer AS gabinet, c.nazwa_uslugi, c.cena, 
               dm.wywiad_lekarski, dm.kod_icd10, icd.nazwa AS icd10_nazwa 
        FROM wizyty w 
        JOIN grafiki_pracy gp ON w.grafik_id = gp.id 
        JOIN pacjenci p ON w.pacjent_id = p.id 
        JOIN gabinety g ON gp.gabinet_id = g.id 
        JOIN cennik c ON w.cennik_id = c.id 
        LEFT JOIN dokumentacja_medyczna dm ON w.id = dm.wizyta_id 
        LEFT JOIN slownik_icd10 icd ON dm.kod_icd10 = icd.kod 
        WHERE gp.lekarz_id = :lid 
          AND w.status = 'Zakończona' 
        ORDER BY gp.termin_od DESC
    """), {"lid": lekarz.id}).fetchall()
    
    return {
        "wizyty": [
            {
                "id": w.id, 
                "status": w.status, 
                "termin_od": w.termin_od.isoformat(), 
                "termin_do": w.termin_do.isoformat(), 
                "pacjent": f"{w.pacjent_imie} {w.pacjent_nazwisko}", 
                "pacjent_pesel": w.pesel, 
                "gabinet": w.gabinet, 
                "nazwa_uslugi": w.nazwa_uslugi, 
                "cena": str(w.cena), 
                "dokumentacja": {
                    "wywiad_lekarski": w.wywiad_lekarski, 
                    "kod_icd10": w.kod_icd10, 
                    "icd10_nazwa": w.icd10_nazwa
                } if w.kod_icd10 or w.wywiad_lekarski else None
            } for w in wizyty
        ]
    }

# wyszukuje profil pacjenta na podstawie zapytania
@router.get("/api/lekarz/pacjent")
def kartoteka_pacjenta(q: str = Query(..., min_length=2), db: Session = Depends(get_db), payload: dict = Depends(tylko_lekarz)):
    wyniki = db.execute(text("""
        SELECT p.id, p.imie, p.nazwisko, p.pesel, p.telefon, 
               a.miejscowosc, a.kod_pocztowy, a.ulica, a.nr_domu, a.nr_lokalu 
        FROM pacjenci p 
        LEFT JOIN adresy a ON p.adres_id = a.id 
        WHERE p.imie ILIKE :q 
           OR p.nazwisko ILIKE :q 
           OR CONCAT(p.imie, ' ', p.nazwisko) ILIKE :q 
           OR p.pesel LIKE :q_exact 
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
                "telefon": w.telefon, 
                "adres": {
                    "miejscowosc": w.miejscowosc, 
                    "kod_pocztowy": w.kod_pocztowy, 
                    "ulica": w.ulica, 
                    "nr_domu": w.nr_domu, 
                    "nr_lokalu": w.nr_lokalu
                }
            } for w in wyniki
        ]
    }

# pobiera szczegolowe informacje o konkretnej wizycie
@router.get("/api/lekarz/wizyty/{wizyta_id}")
def szczegoly_wizyty_lekarz(wizyta_id: int, db: Session = Depends(get_db), payload: dict = Depends(tylko_lekarz)):
    lekarz = db.execute(text("SELECT id FROM lekarze WHERE uzytkownik_id = :uid"), {"uid": payload.get("id")}).fetchone()
    
    wynik = db.execute(text("""
        SELECT w.id, w.status, gp.termin_od, gp.termin_do, g.numer AS gabinet, gp.lekarz_id, 
               p.imie AS pacjent_imie, p.nazwisko AS pacjent_nazwisko, 
               p.pesel AS pacjent_pesel, p.telefon AS pacjent_telefon, 
               CONCAT(COALESCE(a.ulica || ' ', ''), a.nr_domu, COALESCE('/' || a.nr_lokalu, ''), ', ', a.kod_pocztowy, ' ', a.miejscowosc) AS pacjent_adres, 
               dm.kod_icd10, dm.wywiad_lekarski 
        FROM wizyty w 
        JOIN grafiki_pracy gp ON w.grafik_id = gp.id 
        JOIN pacjenci p ON w.pacjent_id = p.id 
        JOIN gabinety g ON gp.gabinet_id = g.id 
        LEFT JOIN adresy a ON p.adres_id = a.id 
        LEFT JOIN dokumentacja_medyczna dm ON dm.wizyta_id = w.id 
        WHERE w.id = :wizyta_id
    """), {"wizyta_id": wizyta_id}).fetchone()
    
    if not wynik: 
        raise HTTPException(status_code=404, detail="Wizyta nie istnieje")
    if wynik.lekarz_id != lekarz.id: 
        raise HTTPException(status_code=403, detail="Brak dostępu do wizyty innego lekarza")
        
    return {
        "id": wynik.id, 
        "status": wynik.status, 
        "termin_od": wynik.termin_od.isoformat(), 
        "termin_do": wynik.termin_do.isoformat(), 
        "gabinet": wynik.gabinet, 
        "pacjent": {
            "imie": wynik.pacjent_imie, 
            "nazwisko": wynik.pacjent_nazwisko, 
            "pesel": wynik.pacjent_pesel, 
            "telefon": wynik.pacjent_telefon, 
            "adres": wynik.pacjent_adres
        }, 
        "dokumentacja": {
            "kod_icd10": wynik.kod_icd10, 
            "wywiad_lekarski": wynik.wywiad_lekarski
        } if (wynik.kod_icd10 or wynik.wywiad_lekarski) else None
    }

# dostarcza systemowi podpowiedzi podczas wyszukiwania kodu choroby
@router.get("/api/slownik/icd10")
def szukaj_icd10(szukaj: str = Query(..., min_length=1), db: Session = Depends(get_db), payload: dict = Depends(tylko_lekarz)):
    wyniki = db.execute(text("""
        SELECT kod, nazwa 
        FROM slownik_icd10 
        WHERE kod ILIKE :q 
           OR nazwa ILIKE :q 
        ORDER BY CASE WHEN kod ILIKE :q_start THEN 1 ELSE 2 END, kod ASC 
        LIMIT 30;
    """), {"q": f"%{szukaj}%", "q_start": f"{szukaj}%"}).fetchall()
    
    return [{"kod": r.kod, "nazwa": r.nazwa} for r in wyniki]

# dodaje rozpoznanie i zamyka wizyte
@router.post("/api/lekarz/wizyty/{wizyta_id}/dokumentacja")
def zapisz_dokumentacje(wizyta_id: int, request: DokumentacjaRequest, db: Session = Depends(get_db), payload: dict = Depends(tylko_lekarz)):
    lekarz = db.execute(text("SELECT id FROM lekarze WHERE uzytkownik_id = :uid"), {"uid": payload.get("id")}).fetchone()
    
    wizyta = db.execute(text("""
        SELECT w.id, w.status, gp.lekarz_id 
        FROM wizyty w 
        JOIN grafiki_pracy gp ON w.grafik_id = gp.id 
        WHERE w.id = :wizyta_id
    """), {"wizyta_id": wizyta_id}).fetchone()
    
    if not wizyta: 
        raise HTTPException(status_code=404, detail="Wizyta nie istnieje")
    if wizyta.lekarz_id != lekarz.id: 
        raise HTTPException(status_code=403, detail="Odmowa dostępu do wizyty innego lekarza")
    if wizyta.status != "Zaplanowana": 
        raise HTTPException(status_code=400, detail="Nie można edytować dokumentacji — wizyta jest zakończona, odwołana lub przeterminowana.")

    try:
        wywiad_json = json.dumps(request.wywiad_lekarski) if request.wywiad_lekarski else None
        
        doc = db.execute(text("SELECT id FROM dokumentacja_medyczna WHERE wizyta_id = :w_id"), {"w_id": wizyta_id}).fetchone()
        
        if doc:
            db.execute(text("""
                UPDATE dokumentacja_medyczna 
                SET kod_icd10 = :icd10, wywiad_lekarski = :wywiad 
                WHERE wizyta_id = :w_id
            """), {"icd10": request.kod_icd10, "wywiad": wywiad_json, "w_id": wizyta_id})
        else:
            db.execute(text("""
                INSERT INTO dokumentacja_medyczna (wizyta_id, kod_icd10, wywiad_lekarski) 
                VALUES (:w_id, :icd10, :wywiad)
            """), {"w_id": wizyta_id, "icd10": request.kod_icd10, "wywiad": wywiad_json})
        
        db.execute(text("""
            UPDATE wizyty 
            SET status = 'Zakończona' 
            WHERE id = :w_id
        """), {"w_id": wizyta_id})
        
        db.commit()
        return {"message": "Dokumentacja medyczna została pomyślnie zapisana, a wizyta zakończona."}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Błąd zapisu dokumentacji: {str(e)}")