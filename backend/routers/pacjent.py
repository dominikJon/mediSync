from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from database import get_db
from dependencies import tylko_pacjent

router = APIRouter(tags=["Pacjent"])

# pobiera dane profilu pacjenta oraz podsumowanie jego wizyt
@router.get("/api/pacjent/profil")
def profil_pacjenta(db: Session = Depends(get_db), payload: dict = Depends(tylko_pacjent)):
    pacjent = db.execute(text("""
        SELECT p.id, p.imie, p.nazwisko, p.pesel, p.telefon, 
               a.miejscowosc, a.kod_pocztowy, a.ulica, a.nr_domu, a.nr_lokalu 
        FROM pacjenci p 
        LEFT JOIN adresy a ON p.adres_id = a.id 
        WHERE p.uzytkownik_id = :uid
    """), {"uid": payload["id"]}).fetchone()
    
    if not pacjent: 
        raise HTTPException(status_code=404, detail="Nie znaleziono profilu pacjenta")

    najblizsa = db.execute(text("""
        SELECT w.id, w.status, g.termin_od, g.termin_do, 
               l.imie AS lekarz_imie, l.nazwisko AS lekarz_nazwisko, 
               s.nazwa AS specjalizacja, gab.numer AS gabinet, 
               c.nazwa_uslugi, c.cena 
        FROM wizyty w 
        JOIN grafiki_pracy g ON w.grafik_id = g.id 
        JOIN lekarze l ON g.lekarz_id = l.id 
        LEFT JOIN lekarz_specjalizacja ls ON l.id = ls.lekarz_id 
        LEFT JOIN specjalizacje s ON ls.specjalizacja_id = s.id 
        JOIN gabinety gab ON g.gabinet_id = gab.id 
        JOIN cennik c ON w.cennik_id = c.id 
        WHERE w.pacjent_id = :pid 
          AND g.termin_od > NOW() 
          AND w.status = 'Zaplanowana' 
        ORDER BY g.termin_od ASC 
        LIMIT 1
    """), {"pid": pacjent.id}).fetchone()
    
    ostatnie = db.execute(text("""
        SELECT w.id, w.status, g.termin_od, g.termin_do, 
               l.imie AS lekarz_imie, l.nazwisko AS lekarz_nazwisko, 
               s.nazwa AS specjalizacja, c.nazwa_uslugi, c.cena 
        FROM wizyty w 
        JOIN grafiki_pracy g ON w.grafik_id = g.id 
        JOIN lekarze l ON g.lekarz_id = l.id 
        LEFT JOIN lekarz_specjalizacja ls ON l.id = ls.lekarz_id 
        LEFT JOIN specjalizacje s ON ls.specjalizacja_id = s.id 
        JOIN cennik c ON w.cennik_id = c.id 
        WHERE w.pacjent_id = :pid 
          AND g.termin_od < NOW() 
        ORDER BY g.termin_od DESC 
        LIMIT 3
    """), {"pid": pacjent.id}).fetchall()

    def wizyta_dict(w): 
        return {
            "id": w.id, 
            "status": w.status, 
            "termin_od": str(w.termin_od), 
            "termin_do": str(w.termin_do), 
            "lekarz": f"{w.lekarz_imie} {w.lekarz_nazwisko}", 
            "specjalizacja": w.specjalizacja, 
            "nazwa_uslugi": w.nazwa_uslugi, 
            "cena": str(w.cena)
        }

    return {
        "pacjent": {
            "id": pacjent.id, 
            "imie": pacjent.imie, 
            "nazwisko": pacjent.nazwisko, 
            "pesel": pacjent.pesel, 
            "telefon": pacjent.telefon, 
            "adres": {
                "miejscowosc": pacjent.miejscowosc, 
                "kod_pocztowy": pacjent.kod_pocztowy, 
                "ulica": pacjent.ulica, 
                "nr_domu": pacjent.nr_domu, 
                "nr_lokalu": pacjent.nr_lokalu
            }
        }, 
        "najblizsa_wizyta": {**wizyta_dict(najblizsa), "gabinet": najblizsa.gabinet} if najblizsa else None, 
        "ostatnie_wizyty": [wizyta_dict(w) for w in ostatnie]
    }

# pobiera historie wizyt pacjenta z opcjonalnym filtrowaniem po statusie
@router.get("/api/pacjent/historia")
def historia_wizyt(status: Optional[str] = None, db: Session = Depends(get_db), payload: dict = Depends(tylko_pacjent)):
    pacjent = db.execute(text("""
        SELECT id 
        FROM pacjenci 
        WHERE uzytkownik_id = :uid
    """), {"uid": payload["id"]}).fetchone()
    
    if not pacjent: 
        raise HTTPException(status_code=404, detail="Nie znaleziono profilu pacjenta")

    warunek_statusu = "AND w.status = :status" if status else ""
    
    wizyty = db.execute(text(f"""
        SELECT w.id, w.status, g.termin_od, g.termin_do, 
               l.imie AS lekarz_imie, l.nazwisko AS lekarz_nazwisko, 
               s.nazwa AS specjalizacja, gab.numer AS gabinet, 
               c.nazwa_uslugi, c.cena, 
               dm.wywiad_lekarski, dm.kod_icd10, 
               icd.nazwa AS icd10_nazwa 
        FROM wizyty w 
        JOIN grafiki_pracy g ON w.grafik_id = g.id 
        JOIN lekarze l ON g.lekarz_id = l.id 
        LEFT JOIN lekarz_specjalizacja ls ON l.id = ls.lekarz_id 
        LEFT JOIN specjalizacje s ON ls.specjalizacja_id = s.id 
        JOIN gabinety gab ON g.gabinet_id = gab.id 
        JOIN cennik c ON w.cennik_id = c.id 
        LEFT JOIN dokumentacja_medyczna dm ON w.id = dm.wizyta_id 
        LEFT JOIN slownik_icd10 icd ON dm.kod_icd10 = icd.kod 
        WHERE w.pacjent_id = :pid 
        {warunek_statusu} 
        ORDER BY g.termin_od DESC
    """), {"pid": pacjent.id, **({"status": status} if status else {})}).fetchall()

    return {
        "wizyty": [
            {
                "id": w.id, 
                "status": w.status, 
                "termin_od": str(w.termin_od), 
                "termin_do": str(w.termin_do), 
                "lekarz": f"{w.lekarz_imie} {w.lekarz_nazwisko}", 
                "specjalizacja": w.specjalizacja, 
                "gabinet": w.gabinet, 
                "nazwa_uslugi": w.nazwa_uslugi, 
                "cena": str(w.cena), 
                "dokumentacja": {
                    "wywiad_lekarski": w.wywiad_lekarski, 
                    "kod_icd10": w.kod_icd10, 
                    "icd10_nazwa": w.icd10_nazwa
                } if w.wywiad_lekarski or w.kod_icd10 else None
            } for w in wizyty
        ]
    }