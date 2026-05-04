from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, Numeric, Text, Enum
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import JSONB
import datetime
import enum

Base = declarative_base()

class User(Base):
    __tablename__ = "role"
    id = Column(Integer, primary_key=True, index=True)
    nazwa = Column(String, unique=True, nullable=False)

class Uzytkownik(Base):
    __tablename__ = "uzytkownik"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    haslo_hash = Column(String(255), nullable=False)
    rola_id = Column(Integer, ForeignKey("role.id"), nullable=False)
    aktywny = Column(Integer, default=1)  # 1 - aktywny, 0 - nieaktywny

# --- Profile Użytkownika ---

class Pacjent(Base):
    __tablename__ = "pacjenci"
    id = Column(Integer, primary_key=True, index=True)
    uzytkownik_id = Column(Integer, ForeignKey("uzytkownik.id"), nullable=False)
    pasel = Column(String(11), unique=True, index=True, nullable=False)
    imie = Column(String(50), nullable=False)
    nazwisko = Column(String(100), nullable=False)
    telefon = Column(String(15))

class Lekarz(Base):
    __tablename__ = "lekarze"
    id = Column(Integer, primary_key=True, index=True)
    uzytkownik_id = Column(Integer, ForeignKey("uzytkownik.id"), nullable=False)
    imie = Column(String(50), nullable=False)
    nazwisko = Column(String(100), nullable=False)
    npwz = Column(String(7), unique=True, nullable=False)
    data_waznosci_oc = Column(Date, nullable=False)
    numer_uprawnien = Column(String(20), unique=True, index=True, nullable=False)

# --- Harmonogramy i Wizyty ---

class Gabinet(Base):
    __tablename__ = "gabinet"
    id = Column(Integer, primary_key=True, index=True)
    nazwa = Column(String(10), nullable=False, unique=True)
    status = Column(String(20), default="Dostępny")

class GrafikPracy(Base):
    __tablename__ = "grafik_pracy"
    id = Column(Integer, primary_key=True, index=True)
    lekarz_id = Column(Integer, ForeignKey("lekarze.id"), nullable=False)
    gabinet_id = Column(Integer, ForeignKey("gabinet.id"), nullable=False)
    termin_od = Column(DateTime, nullable=False)
    termin_do = Column(DateTime, nullable=False)
    zarezrwany = Column(Integer, default=0)  # 0 - wolny, 1 - zarezerwowany

class StatusWizyty(enum.Enum):
    ZAPLANOWANA = "Zaplanowana"
    W_TRAKCIE = "W trakcie"
    ODWOLANA = "Odwołana"
    ZAKONCZONA = "Zakończona"

class Wizyta(Base):
    __tablename__ = "wizyta"
    id = Column(Integer, primary_key=True, index=True)
    pacjent_id = Column(Integer, ForeignKey("pacjenci.id"), nullable=False)
    grafik_pracy_id = Column(Integer, ForeignKey("grafik_pracy.id"), nullable=False)
    status = Column(Enum(StatusWizyty), default=StatusWizyty.ZAPLANOWANA)
    data_utworzenia = Column(DateTime, default=datetime.datetime.utcnow)

# --- EDM, JAKŚĆ i PRAWO ---

class DokumentacjaMedyczna(Base):
    __tablename__ = "dokumentacja_medyczna"
    id = Column(Integer, primary_key=True, index=True)
    wizyta_id = Column(Integer, ForeignKey("wizyty.id"), unique=True, nullable=False)
    wywiad = Column(JSONB, nullable=True) # <-- CZYSTY JSONB (wymóg dokumentacji)
    kod_icd10 = Column(String(10), nullable=True) # Diagnoza
    data_wpisu = Column(DateTime, default=datetime.datetime.utcnow)

class ZdarzenieNiepozadane(Base):
    __tablename__ = "zdarzenia_niepozadane"
    id = Column(Integer, primary_key=True, index=True)
    pacjent_id = Comlumn(Integer, ForeignKey("pacjenci.id"), nullable=False)
    imie_upowaznionego = Column(String(50), nullable=False)
    nazwisko_upowaznionego = Column(String(100), nullable=False)
    pesel_upowaznionego = Column(String(11), nullable=False)

# --- Finanse ---
class Cennik(Base):
    __tablename__ = "cennik"
    id = Column(Integer, primary_key=True, index=True)
    nazwa_uslugi = Column(String(150), nullable=False)
    cena = Column(Numeric(10, 2), nullable=False)
    data_od = Column(Date, nullable=False)
    data_do = Column(Date, nullable=True)