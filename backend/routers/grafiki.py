from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date, datetime, timedelta

from database import get_db
from models.schemas import DodajGrafikRequest
from dependencies import tylko_admin_lub_rejestracja

router = APIRouter(tags=["Grafiki Pracy i Pulpit Recepcji"])

# pobiera statystyki i dane na pulpit recepcji
@router.get("/api/reception/pulpit")
def pulpit_rejestracji(db: Session = Depends(get_db), payload: dict = Depends(tylko_admin_lub_rejestracja)):
    wizyty_dzis = db.execute(text("""
        SELECT 
            COUNT(*) FILTER (WHERE w.status = 'Zaplanowana') AS zaplanowane, 
            COUNT(*) FILTER (WHERE w.status = 'Zakończona') AS zakonczone, 
            COUNT(*) FILTER (WHERE w.status = 'Odwołana') AS odwolane 
        FROM wizyty w 
        JOIN grafiki_pracy gp ON w.grafik_id = gp.id 
        WHERE DATE(gp.termin_od) = CURRENT_DATE
    """)).fetchone()
    
    lista_dzis = db.execute(text("""
        SELECT w.id, w.status, gp.termin_od, gp.termin_do, 
               p.imie AS pacjent_imie, p.nazwisko AS pacjent_nazwisko, 
               l.imie AS lekarz_imie, l.nazwisko AS lekarz_nazwisko, 
               g.numer AS gabinet 
        FROM wizyty w 
        JOIN grafiki_pracy gp ON w.grafik_id = gp.id 
        JOIN pacjenci p ON w.pacjent_id = p.id 
        JOIN lekarze l ON gp.lekarz_id = l.id 
        JOIN gabinety g ON gp.gabinet_id = g.id 
        WHERE DATE(gp.termin_od) = CURRENT_DATE 
          AND w.status = 'Zaplanowana' 
        ORDER BY gp.termin_od ASC 
        LIMIT 8
    """)).fetchall()
    
    lekarze_dzis = db.execute(text("""
        SELECT DISTINCT l.imie, l.nazwisko, 
               array_agg(DISTINCT g.numer) AS gabinety, 
               COUNT(gp.id) AS liczba_slotow, 
               COUNT(w.id) AS zajete_sloty 
        FROM grafiki_pracy gp 
        JOIN lekarze l ON gp.lekarz_id = l.id 
        JOIN gabinety g ON gp.gabinet_id = g.id 
        LEFT JOIN wizyty w ON gp.id = w.grafik_id AND w.status = 'Zaplanowana' 
        WHERE DATE(gp.termin_od) = CURRENT_DATE 
        GROUP BY l.id, l.imie, l.nazwisko 
        ORDER BY l.nazwisko
    """)).fetchall()
    
    wolne_sloty = db.execute(text("""
        SELECT COUNT(*) AS liczba 
        FROM grafiki_pracy gp 
        LEFT JOIN wizyty w ON gp.id = w.grafik_id AND w.status = 'Zaplanowana' 
        WHERE DATE(gp.termin_od) = CURRENT_DATE 
          AND w.id IS NULL
    """)).fetchone()
    
    return {
        "wizyty_dzis": {
            "zaplanowane": wizyty_dzis.zaplanowane, 
            "zakonczone": wizyty_dzis.zakonczone, 
            "odwolane": wizyty_dzis.odwolane
        }, 
        "lista_dzis": [
            {
                "id": w.id, 
                "termin_od": w.termin_od.isoformat(), 
                "termin_do": w.termin_do.isoformat(), 
                "pacjent": f"{w.pacjent_imie} {w.pacjent_nazwisko}", 
                "lekarz": f"dr {w.lekarz_imie} {w.lekarz_nazwisko}", 
                "gabinet": w.gabinet, 
                "status": w.status
            } for w in lista_dzis
        ], 
        "lekarze_dzis": [
            {
                "lekarz": f"dr {l.imie} {l.nazwisko}", 
                "gabinety": l.gabinety, 
                "liczba_slotow": l.liczba_slotow, 
                "zajete_sloty": l.zajete_sloty, 
                "wolne_sloty": l.liczba_slotow - l.zajete_sloty
            } for l in lekarze_dzis
        ], 
        "wolne_sloty_dzis": wolne_sloty.liczba
    }

# zwraca liste lekarzy na potrzeby pracownika recepcji
@router.get("/api/reception/lekarze")
def lista_lekarzy(db: Session = Depends(get_db), payload: dict = Depends(tylko_admin_lub_rejestracja)):
    wyniki = db.execute(text("""
        SELECT l.id, l.imie, l.nazwisko, array_remove(array_agg(s.nazwa), NULL) AS specjalizacje 
        FROM lekarze l 
        JOIN uzytkownicy u ON l.uzytkownik_id = u.id 
        LEFT JOIN lekarz_specjalizacja ls ON l.id = ls.lekarz_id 
        LEFT JOIN specjalizacje s ON ls.specjalizacja_id = s.id 
        GROUP BY l.id, l.imie, l.nazwisko 
        ORDER BY l.nazwisko, l.imie
    """)).fetchall()
    
    return {
        "lekarze": [
            {
                "id": w.id, 
                "imie": w.imie, 
                "nazwisko": w.nazwisko, 
                "specjalizacje": w.specjalizacje
            } for w in wyniki
        ]
    }

# pobiera grafik pracy placowki na konkretny dzien
@router.get("/api/reception/grafiki")
def lista_grafiku(data: date = Query(..., description="Data w formacie YYYY-MM-DD"), db: Session = Depends(get_db), payload: dict = Depends(tylko_admin_lub_rejestracja)):
    wyniki = db.execute(text("""
        SELECT gp.id, l.imie AS lekarz_imie, l.nazwisko AS lekarz_nazwisko, 
               g.numer AS gabinet_numer, gp.termin_od, gp.termin_do, 
               CASE WHEN w.id IS NOT NULL THEN true ELSE false END AS zajety 
        FROM grafiki_pracy gp 
        JOIN lekarze l ON gp.lekarz_id = l.id 
        JOIN gabinety g ON gp.gabinet_id = g.id 
        LEFT JOIN wizyty w ON w.grafik_id = gp.id 
        WHERE DATE(gp.termin_od) = :data 
        ORDER BY gp.termin_od, l.nazwisko
    """), {"data": data}).fetchall()
    
    return {
        "grafiki": [
            {
                "id": w.id, 
                "lekarz": f"{w.lekarz_imie} {w.lekarz_nazwisko}", 
                "gabinet": w.gabinet_numer, 
                "termin_od": w.termin_od, 
                "termin_do": w.termin_do, 
                "zajety": w.zajety
            } for w in wyniki
        ]
    }

# generuje i dodaje nowe sloty wizyt do grafiku pracy
@router.post("/api/reception/grafiki", status_code=201)
def dodaj_grafik(request: DodajGrafikRequest, db: Session = Depends(get_db), payload: dict = Depends(tylko_admin_lub_rejestracja)):
    try:
        h_od, m_od = map(int, request.godzina_od.split(":"))
        h_do, m_do = map(int, request.godzina_do.split(":"))
        poczatek_bloku = datetime(request.data.year, request.data.month, request.data.day, h_od, m_od)
        koniec_bloku = datetime(request.data.year, request.data.month, request.data.day, h_do, m_do)
        
        kolizja = db.execute(text("""
            SELECT id 
            FROM grafiki_pracy 
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
            raise HTTPException(status_code=409, detail="Wykryto kolizję! Lekarz lub gabinet jest już zajęty w tym przedziale czasowym.")
        
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
            
        db.execute(text("""
            INSERT INTO grafiki_pracy (lekarz_id, gabinet_id, termin_od, termin_do) 
            VALUES (:lekarz_id, :gabinet_id, :termin_od, :termin_do)
        """), sloty)
        
        db.commit()
        return {"status": "sukces", "dodano_slotow": len(sloty)}
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Błąd podczas generowania grafiku: {str(e)}")

# usuwa wolny slot z grafiku
@router.delete("/api/reception/grafiki/{grafik_id}")
def usun_slot_grafiku(grafik_id: int, db: Session = Depends(get_db), payload: dict = Depends(tylko_admin_lub_rejestracja)):
    try:
        slot = db.execute(text("""
            SELECT id 
            FROM grafiki_pracy 
            WHERE id = :id
        """), {"id": grafik_id}).fetchone()
        
        if not slot: 
            raise HTTPException(status_code=404, detail="Podany slot nie istnieje")
            
        wizyta = db.execute(text("""
            SELECT id 
            FROM wizyty 
            WHERE grafik_id = :grafik_id
        """), {"grafik_id": grafik_id}).fetchone()
        
        if wizyta: 
            raise HTTPException(status_code=409, detail="Nie można usunąć — slot ma już przypisaną wizytę!")
            
        db.execute(text("""
            DELETE FROM grafiki_pracy 
            WHERE id = :id
        """), {"id": grafik_id})
        
        db.commit()
        return {"status": "sukces", "wiadomosc": "Slot został pomyślnie usunięty"}
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Błąd podczas usuwania slotu: {str(e)}")