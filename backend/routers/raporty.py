from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date

from database import get_db
from dependencies import tylko_admin, kazdy_zalogowany

router = APIRouter(tags=["Raporty Admina"])

# pobiera ogolne statystyki systemu dla administratora
@router.get("/api/admin/raporty/summary")
def raport_summary(db: Session = Depends(get_db), payload: dict = Depends(tylko_admin)):
    pacjenci = db.execute(text("SELECT COUNT(*) FROM pacjenci")).scalar()
    lekarze = db.execute(text("SELECT COUNT(*) FROM lekarze")).scalar()
    
    wizyty_dzis = db.execute(text("""
        SELECT COUNT(*) 
        FROM wizyty w 
        JOIN grafiki_pracy gp ON w.grafik_id = gp.id 
        WHERE DATE(gp.termin_od) = CURRENT_DATE
    """)).scalar()
    
    wizyty_miesiac = db.execute(text("""
        SELECT COUNT(*) 
        FROM wizyty w 
        JOIN grafiki_pracy gp ON w.grafik_id = gp.id 
        WHERE DATE_TRUNC('month', gp.termin_od) = DATE_TRUNC('month', NOW())
    """)).scalar()
    
    return {
        "pacjenci": pacjenci or 0, 
        "lekarze": lekarze or 0, 
        "wizyty_dzis": wizyty_dzis or 0, 
        "wizyty_miesiac": wizyty_miesiac or 0
    }

# generuje szczegolowy raport wizyt w wybranym przedziale czasowym
@router.get("/api/admin/raporty/wizyty")
def raport_wizyty(od: date = Query(...), do_daty: date = Query(..., alias="do"), db: Session = Depends(get_db), payload: dict = Depends(tylko_admin)):
    if od > do_daty: 
        raise HTTPException(status_code=400, detail="Data 'od' nie może być późniejsza niż 'do'")
        
    statusy = db.execute(text("""
        SELECT w.status, COUNT(*) AS liczba 
        FROM wizyty w 
        JOIN grafiki_pracy gp ON w.grafik_id = gp.id 
        WHERE DATE(gp.termin_od) BETWEEN :od AND :do 
        GROUP BY w.status 
        ORDER BY liczba DESC
    """), {"od": od, "do": do_daty}).fetchall()
    
    lacznie = sum(r.liczba for r in statusy)
    
    per_lekarz = db.execute(text("""
        SELECT l.imie, l.nazwisko, array_remove(array_agg(DISTINCT s.nazwa), NULL) AS specjalizacje, 
               COUNT(w.id) AS wszystkie, 
               COUNT(CASE WHEN w.status = 'Zakończona' THEN 1 END) AS zakonczone, 
               COUNT(CASE WHEN w.status = 'Odwołana' THEN 1 END) AS odwolane, 
               COUNT(CASE WHEN w.status = 'Nieobecność' THEN 1 END) AS nieobecnosci, 
               COUNT(CASE WHEN w.status = 'Zaplanowana' THEN 1 END) AS zaplanowane 
        FROM wizyty w 
        JOIN grafiki_pracy gp ON w.grafik_id = gp.id 
        JOIN lekarze l ON gp.lekarz_id = l.id 
        LEFT JOIN lekarz_specjalizacja ls ON l.id = ls.lekarz_id 
        LEFT JOIN specjalizacje s ON ls.specjalizacja_id = s.id 
        WHERE DATE(gp.termin_od) BETWEEN :od AND :do 
        GROUP BY l.id, l.imie, l.nazwisko 
        ORDER BY wszystkie DESC
    """), {"od": od, "do": do_daty}).fetchall()
    
    return {
        "okres": {
            "od": str(od), 
            "do": str(do_daty)
        }, 
        "lacznie": lacznie, 
        "per_status": [
            {
                "status": r.status, 
                "liczba": r.liczba, 
                "procent": round(r.liczba / lacznie * 100, 1) if lacznie else 0
            } for r in statusy
        ], 
        "per_lekarz": [
            {
                "lekarz": f"dr {r.imie} {r.nazwisko}", 
                "specjalizacje": r.specjalizacje if r.specjalizacje else [], 
                "wszystkie": r.wszystkie, 
                "zakonczone": r.zakonczone, 
                "odwolane": r.odwolane, 
                "nieobecnosci": r.nieobecnosci, 
                "zaplanowane": r.zaplanowane
            } for r in per_lekarz
        ]
    }

#endpoint do cennika dla pacjentow na pulpicie 
@router.get("/api/cennik")
def pobierz_cennik(db: Session = Depends(get_db), payload: dict = Depends(kazdy_zalogowany)):
    wyniki = db.execute(text("""
        SELECT c.id, c.nazwa_uslugi, c.cena, s.nazwa AS specjalizacja
        FROM cennik c
        LEFT JOIN specjalizacje s ON c.specjalizacja_id = s.id
        WHERE c.data_do IS NULL OR c.data_do > NOW()
        ORDER BY c.cena ASC
    """)).fetchall()

    return {
        "cennik": [
            {
                "id": w.id,
                "nazwa_uslugi": w.nazwa_uslugi,
                "cena": float(w.cena),
                "specjalizacja": w.specjalizacja,
            }
            for w in wyniki
        ]
    }