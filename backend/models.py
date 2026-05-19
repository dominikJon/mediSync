from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, Numeric, Text, Table, Boolean
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import JSONB
import datetime

Base = declarative_base()

# --- TABELE ASOCJACYJNE (Wiele-do-wielu) ---
lekarz_specjalizacja_table = Table(
    "lekarz_specjalizacja",
    Base.metadata,
    Column("lekarz_id", Integer, ForeignKey("lekarze.id"), primary_key=True),
    Column("specjalizacja_id", Integer, ForeignKey("specjalizacje.id"), primary_key=True)
)

# --- SŁOWNIKI I SYSTEM ---

class Rola(Base):
    __tablename__ = "role"
    id = Column(Integer, primary_key=True, index=True)
    nazwa = Column(String(50), unique=True, nullable=False)

    uzytkownicy = relationship("Uzytkownik", back_populates="rola")

class Uzytkownik(Base):
    __tablename__ = "uzytkownicy" 
    id = Column(Integer, primary_key=True, index=True)
    rola_id = Column(Integer, ForeignKey("role.id"), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    haslo_hash = Column(String(255), nullable=False)
    profil_uzupelniony = Column(Boolean, default=False)  

    rola = relationship("Rola", back_populates="uzytkownicy")
    pacjent_profil = relationship("Pacjent", back_populates="konto", uselist=False)
    lekarz_profil = relationship("Lekarz", back_populates="konto", uselist=False)
    pracownik_profil = relationship("Pracownik", back_populates="konto", uselist=False)

# --- MODUŁ PLACÓWKI, ADRESÓW I PERSONELU ---

class Adres(Base):
    __tablename__ = "adresy"
    id = Column(Integer, primary_key=True, index=True)
    miejscowosc = Column(String(100), nullable=False)
    kod_pocztowy = Column(String(6), nullable=False)
    ulica = Column(String(100), nullable=True)
    nr_domu = Column(String(10), nullable=False)
    nr_lokalu = Column(String(10), nullable=True)

    pacjenci = relationship("Pacjent", back_populates="adres")

class Placowka(Base):
    __tablename__ = "placowki"
    id = Column(Integer, primary_key=True, index=True)
    nazwa = Column(String(200), nullable=False)
    nr_ksiegi_rpwdl = Column(String(50), nullable=False)
    autoryzacja_mz_do = Column(Date, nullable=True)
    autoryzacja_nfz_do = Column(Date, nullable=True)

    lekarze = relationship("Lekarz", back_populates="placowka")

class Specjalizacja(Base):
    __tablename__ = "specjalizacje"
    id = Column(Integer, primary_key=True, index=True)
    nazwa = Column(String(100), nullable=False)

    lekarze = relationship("Lekarz", secondary=lekarz_specjalizacja_table, back_populates="specjalizacje")

class Lekarz(Base):
    __tablename__ = "lekarze"
    id = Column(Integer, primary_key=True, index=True)
    imie = Column(String(50), nullable=True)       
    nazwisko = Column(String(100), nullable=True)
    pesel = Column(String(11), nullable=True)
    telefon = Column(String(15))  
    uzytkownik_id = Column(Integer, ForeignKey("uzytkownicy.id"), nullable=False)
    placowka_id = Column(Integer, ForeignKey("placowki.id"), nullable=False)
    npwz = Column(String(7), unique=True, nullable=False)
    status_npwz = Column(String(50), nullable=False) 
    waznosc_oc = Column(Date, nullable=False)
     

    konto = relationship("Uzytkownik", back_populates="lekarz_profil")
    placowka = relationship("Placowka", back_populates="lekarze")
    specjalizacje = relationship("Specjalizacja", secondary=lekarz_specjalizacja_table, back_populates="lekarze")
    grafiki = relationship("GrafikPracy", back_populates="lekarz")

# --- PROFILE pracownikow ---

class Pracownik(Base):
    __tablename__ = "pracownicy"
    id = Column(Integer, primary_key=True, index=True)
    uzytkownik_id = Column(Integer, ForeignKey("uzytkownicy.id"), nullable=False)
    imie = Column(String(50), nullable=False)
    nazwisko = Column(String(100), nullable=False)
    telefon = Column(String(15))
    pesel = Column(String(11), nullable=True) 

    konto = relationship("Uzytkownik", back_populates="pracownik_profil")


# --- PROFILE UŻYTKOWNIKA ---

class Pacjent(Base):
    __tablename__ = "pacjenci"
    id = Column(Integer, primary_key=True, index=True)
    uzytkownik_id = Column(Integer, ForeignKey("uzytkownicy.id"), nullable=False)
    adres_id = Column(Integer, ForeignKey("adresy.id"), nullable=True)
    pesel = Column(String(11), unique=True, index=True, nullable=False) 
    imie = Column(String(50), nullable=False)
    nazwisko = Column(String(100), nullable=False)
    telefon = Column(String(15))

    konto = relationship("Uzytkownik", back_populates="pacjent_profil")
    adres = relationship("Adres", back_populates="pacjenci")
    wizyty = relationship("Wizyta", back_populates="pacjent")
    upowaznienia = relationship("UpowaznienieMedyczne", back_populates="pacjent")
    zgody = relationship("Zgoda", back_populates="pacjent")

class Zgoda(Base):
    __tablename__ = "zgody"
    id = Column(Integer, primary_key=True, index=True)
    pacjent_id = Column(Integer, ForeignKey("pacjenci.id"), nullable=False)
    typ_zgody = Column(String(100), nullable=False)
    tresc_zgody = Column(Text, nullable=False) 
    data_wyrazenia = Column(DateTime, default=datetime.datetime.utcnow)
    data_wycofania = Column(DateTime, nullable=True)  

    pacjent = relationship("Pacjent", back_populates="zgody")

class UpowaznienieMedyczne(Base): # 
    __tablename__ = "upowaznienia_medyczne"
    id = Column(Integer, primary_key=True, index=True)
    pacjent_id = Column(Integer, ForeignKey("pacjenci.id"), nullable=False)
    imie = Column(String(50), nullable=False)
    nazwisko = Column(String(100), nullable=False)
    pesel = Column(String(11), nullable=False)

    pacjent = relationship("Pacjent", back_populates="upowaznienia")

    

# --- HARMONOGRAMY I WIZYTY ---

class Gabinet(Base):
    __tablename__ = "gabinety"
    id = Column(Integer, primary_key=True, index=True)
    numer = Column(String(10), nullable=False, unique=True) 
    status = Column(String(20), default="Dostępny")

    grafiki = relationship("GrafikPracy", back_populates="gabinet")

class GrafikPracy(Base):
    __tablename__ = "grafiki_pracy"
    id = Column(Integer, primary_key=True, index=True)
    lekarz_id = Column(Integer, ForeignKey("lekarze.id"), nullable=False)
    gabinet_id = Column(Integer, ForeignKey("gabinety.id"), nullable=False)
    termin_od = Column(DateTime, nullable=False)
    termin_do = Column(DateTime, nullable=False)

    lekarz = relationship("Lekarz", back_populates="grafiki")
    gabinet = relationship("Gabinet", back_populates="grafiki")
    wizyty = relationship("Wizyta", back_populates="grafik", uselist=False)

class Wizyta(Base):
    __tablename__ = "wizyty"
    id = Column(Integer, primary_key=True, index=True)
    pacjent_id = Column(Integer, ForeignKey("pacjenci.id"), nullable=False)
    grafik_id = Column(Integer, ForeignKey("grafiki_pracy.id"), unique=True, nullable=False)
    cennik_id = Column(Integer, ForeignKey("cennik.id"), nullable=False)
    status = Column(String(50), default="Zaplanowana") 

    pacjent = relationship("Pacjent", back_populates="wizyty")
    grafik = relationship("GrafikPracy", back_populates="wizyty")
    cennik = relationship("Cennik", back_populates="wizyty")
    dokumentacja = relationship("DokumentacjaMedyczna", back_populates="wizyta", uselist=False)
    transakcja = relationship("Transakcja", back_populates="wizyta", uselist=False) 

# --- EDM, JAKOŚĆ I PRAWO ---

class SlownikICD10(Base):
    __tablename__ = "slownik_icd10"
    kod = Column(String(10), primary_key=True)
    nazwa = Column(String(255), nullable=False)

    dokumentacje = relationship("DokumentacjaMedyczna", back_populates="icd10")

class DokumentacjaMedyczna(Base):
    __tablename__ = "dokumentacja_medyczna"
    id = Column(Integer, primary_key=True, index=True)
    wizyta_id = Column(Integer, ForeignKey("wizyty.id"), unique=True, nullable=False)
    kod_icd10 = Column(String(10), ForeignKey("slownik_icd10.kod"), nullable=True)
    wywiad_lekarski = Column(JSONB, nullable=True) 

    wizyta = relationship("Wizyta", back_populates="dokumentacja")
    icd10 = relationship("SlownikICD10", back_populates="dokumentacje")

class ZdarzenieNiepozadane(Base):
    __tablename__ = "zdarzenia_niepozadane"
    id = Column(Integer, primary_key=True, index=True)
    wizyta_id = Column(Integer, ForeignKey("wizyty.id"), nullable=False)
    kategoria_bledu = Column(String(100), nullable=False)
    opis_incydentu = Column(Text, nullable=False)
    data_zgloszenia = Column(DateTime, default=datetime.datetime.utcnow)    
    status_wyjasnienia = Column(String(50), default="Do wyjaśnienia")

class LogiAudytowe(Base):
    __tablename__ = "logi_audytowe"
    id = Column(Integer, primary_key=True, index=True)
    tabela = Column(String(50), nullable=False)
    operacja = Column(String(50), nullable=False)
    kto_zmienil = Column(Integer, nullable=False)
    data_zmiany = Column(DateTime, default=datetime.datetime.utcnow)
    stare_dane = Column(JSONB, nullable=True)
    nowe_dane = Column(JSONB, nullable=True)
        
# --- FINANSE ---
class Cennik(Base):
    __tablename__ = "cennik"
    id = Column(Integer, primary_key=True, index=True)
    nazwa_uslugi = Column(String(150), nullable=False)
    cena = Column(Numeric(10, 2), nullable=False)
    data_od = Column(DateTime, nullable=False) 
    data_do = Column(DateTime, nullable=True) 

    wizyty = relationship("Wizyta", back_populates="cennik")

class Transakcja(Base):
    __tablename__ = "transakcje"
    id = Column(Integer, primary_key=True, index=True)
    wizyta_id = Column(Integer, ForeignKey("wizyty.id"), unique=True, nullable=False)
    kwota = Column(Numeric(10, 2), nullable=False)
    metoda_platnosci = Column(String(50), nullable=False)
    status = Column(String(50), default="Oczekująca")  

    wizyta = relationship("Wizyta", back_populates="transakcja")