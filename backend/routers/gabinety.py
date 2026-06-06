from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi_mail import MessageSchema

from database import get_db
from models.schemas import DodajGabinetRequest, ZmienStatusGabinetuRequest
from dependencies import tylko_admin_lub_rejestracja, fastmail

router = APIRouter(tags=["Gabinety"])

# pobiera liste wszystkich gabinetow w placowce
@router.get("/api/reception/gabinety")
def lista_gabinetow(db: Session = Depends(get_db), payload: dict = Depends(tylko_admin_lub_rejestracja)):
    wyniki = db.execute(text("""
        SELECT id, numer, status 
        FROM gabinety 
        ORDER BY numer
    """)).fetchall()
    
    return {
        "gabinety": [{"id": w.id, "numer": w.numer, "status": w.status} for w in wyniki]
    }

# dodaje nowy gabinet do systemu
@router.post("/api/reception/gabinety", status_code=201)
def dodaj_gabinet(request: DodajGabinetRequest, db: Session = Depends(get_db), payload: dict = Depends(tylko_admin_lub_rejestracja)):
    try:
        istniejacy = db.execute(text("""
            SELECT id 
            FROM gabinety 
            WHERE numer = :numer
        """), {"numer": request.numer}).fetchone()
        
        if istniejacy:
            raise HTTPException(status_code=409, detail="Gabinet o tym numerze już istnieje")
            
        nowy = db.execute(text("""
            INSERT INTO gabinety (numer, status) 
            VALUES (:numer, :status) 
            RETURNING id
        """), {
            "numer": request.numer, 
            "status": request.status
        }).fetchone()
        
        db.commit()
        return {"status": "sukces", "gabinet_id": nowy.id}
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Błąd podczas dodawania gabinetu: {str(e)}")

# zmienia status gabinetu i anuluje powiazane z nim zaplanowane wizyty
@router.patch("/api/reception/gabinety/{gabinet_id}/status")
async def zmien_status_gabinetu(gabinet_id: int, request: ZmienStatusGabinetuRequest, db: Session = Depends(get_db), payload: dict = Depends(tylko_admin_lub_rejestracja)):
    try:
        gab = db.execute(text("""
            SELECT id, numer, status 
            FROM gabinety 
            WHERE id = :id
        """), {"id": gabinet_id}).fetchone()
        
        if not gab: 
            raise HTTPException(status_code=404, detail="Podany gabinet nie istnieje")
            
        db.execute(text("""
            UPDATE gabinety 
            SET status = :status 
            WHERE id = :id
        """), {
            "status": request.status, 
            "id": gabinet_id
        })
        
        odwolane = []
        
        if request.status == 'Niedostępny' and gab.status == 'Dostępny':
            wizyty = db.execute(text("""
                SELECT w.id, gp.termin_od, 
                       l.imie AS lekarz_imie, l.nazwisko AS lekarz_nazwisko, ul.email AS lekarz_email, 
                       p.imie AS pacjent_imie, p.nazwisko AS pacjent_nazwisko, up.email AS pacjent_email 
                FROM wizyty w 
                JOIN grafiki_pracy gp ON w.grafik_id = gp.id 
                JOIN lekarze l ON gp.lekarz_id = l.id 
                JOIN uzytkownicy ul ON l.uzytkownik_id = ul.id 
                JOIN pacjenci p ON w.pacjent_id = p.id 
                JOIN uzytkownicy up ON p.uzytkownik_id = up.id 
                WHERE gp.gabinet_id = :id 
                  AND gp.termin_od > NOW() 
                  AND w.status = 'Zaplanowana'
            """), {"id": gabinet_id}).fetchall()
            
            for w in wizyty:
                db.execute(text("""
                    UPDATE wizyty 
                    SET status = 'Odwołana' 
                    WHERE id = :id
                """), {"id": w.id})
                
                odwolane.append(w)
                
        db.commit()
        
        rejestracja_maile = db.execute(text("""
            SELECT u.email 
            FROM uzytkownicy u 
            JOIN role r ON u.rola_id = r.id 
            WHERE r.nazwa = 'rejestracja'
        """)).fetchall()
        
        recs = [r.email for r in rejestracja_maile]
        
        for w in odwolane:
            t = w.termin_od.strftime("%d.%m.%Y o %H:%M")
            tabela = f"<table style='border-collapse: collapse; margin: 16px 0;'><tr><td style='padding: 8px 16px 8px 0; color: #64748b; font-weight: 600;'>Pacjent:</td><td style='padding: 8px 0;'>{w.pacjent_imie} {w.pacjent_nazwisko}</td></tr><tr><td style='padding: 8px 16px 8px 0; color: #64748b; font-weight: 600;'>Lekarz:</td><td style='padding: 8px 0;'>dr {w.lekarz_imie} {w.lekarz_nazwisko}</td></tr><tr><td style='padding: 8px 16px 8px 0; color: #64748b; font-weight: 600;'>Termin:</td><td style='padding: 8px 0;'><strong>{t}</strong></td></tr><tr><td style='padding: 8px 16px 8px 0; color: #64748b; font-weight: 600;'>Gabinet:</td><td style='padding: 8px 0;'>{gab.numer}</td></tr></table>"
            
            await fastmail.send_message(MessageSchema(
                subject="Odwołanie wizyty — MediSync", 
                recipients=[w.pacjent_email], 
                body=f"<h2>Odwołanie wizyty — MediSync</h2><p>Drogi/a {w.pacjent_imie} {w.pacjent_nazwisko},</p><p>Twoja wizyta została odwołana z powodu <strong>niedostępności gabinetu {gab.numer}</strong>.</p>{tabela}<p>Przepraszamy za utrudnienia.</p><a href='http://localhost:5173/schedule' style='display: inline-block; padding: 12px 24px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;'>Zarezerwuj nowy termin</a><br><br><p>Zespół MediSync</p>", 
                subtype="html"
            ))
            
            await fastmail.send_message(MessageSchema(
                subject="Odwołanie wizyty — MediSync", 
                recipients=[w.lekarz_email], 
                body=f"<h2>Odwołanie wizyty — MediSync</h2><p>Wizyta została odwołana z powodu <strong>niedostępności gabinetu {gab.numer}</strong>.</p>{tabela}<p>Zespół MediSync</p>", 
                subtype="html"
            ))
            
            if recs: 
                await fastmail.send_message(MessageSchema(
                    subject="Odwołanie wizyty — gabinet niedostępny", 
                    recipients=recs, 
                    body=f"<h2>Automatyczne odwołanie wizyty</h2><p>Gabinet <strong>{gab.numer}</strong> został oznaczony jako niedostępny. Poniższa wizyta została odwołana:</p>{tabela}", 
                    subtype="html"
                ))
                
        return {"status": "sukces", "wiadomosc": f"Status zmieniony", "odwolane_wizyty": len(odwolane)}
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Błąd: {str(e)}")