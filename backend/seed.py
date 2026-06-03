import random
import datetime
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import bcrypt  # <--- Zmieniono z passlib na bezpośredni bcrypt

from models import (
    Base, Rola, Uzytkownik, Pacjent, Lekarz, Pracownik, Adres, 
    Placowka, Specjalizacja, Gabinet, Cennik, SlownikICD10, Zgoda
)

# --- KONFIGURACJA POŁĄCZENIA LOKALNEGO ---
load_dotenv()
DB_PASSWORD = os.getenv("DB_PASSWORD")

if not DB_PASSWORD:
    raise ValueError("Nie można znaleźć hasła do bazy. Upewnij się, że masz plik .env z DB_PASSWORD.")

LOCAL_DB_URL = f"postgresql://admin:{DB_PASSWORD}@localhost:5432/medisync"
engine_local = create_engine(LOCAL_DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_local)

# --- LISTA 100 OSÓB ---
dane_osob = [
    "Adrian Sawicki", "Matvii Szymczak", "Jakub Głowacki", "Ignacy Zając", "Marcin Majewski",
    "Bruno Tomaszewski", "Alan Ziółkowski", "Luiza Marciniak", "Leon Wilk", "Alex Konieczny",
    "Malwina Zając", "Konstanty Krajewski", "Leon Gajewski", "Lena Mróz", "Kornel Szulc",
    "Krzysztof Wilk", "Michał Duda", "Joanna Włodarczyk", "Lea Nowicka", "Emilia Adamczyk",
    "Kuba Kwiatkowski", "Kornelia Szymańska", "Joanna Baranowska", "Leonard Wojciechowski",
    "Sebastian Borowski", "Eryk Kaczmarek", "Karol Krupa", "Alex Brzeziński", "Kalina Pietrzak",
    "Alicja Baran", "Sofiia Górska", "Antonina Kalinowska", "Wiktoria Kamińska", "Lea Mazur",
    "Zoja Kowalczyk", "Felicja Wieczorek", "Leonard Ziółkowski", "Kazimierz Sikora",
    "Marek Krajewski", "Róża Sikorska", "Igor Grabowski", "Radosław Wieczorek", "Emilia Wróbel",
    "Artem Nowakowski", "Lena Mazurek", "Oliwia Kania", "Ewa Kwiatkowska", "Nikola Jasińska",
    "Nikola Gajewska", "Lea Sikorska", "Sofiia Majewska", "Adela Brzezińska", "Dominik Kwiatkowski",
    "Jan Kowalczyk", "Gustaw Sikora", "Oliwia Chmielewska", "Wojciech Ziółkowski", "Karol Wróbel",
    "Celina Stępień", "Kazimierz Lewandowski", "Artem Tomaszewski", "Florian Gajewski",
    "Daria Zielińska", "Borys Włodarczyk", "Nela Baran", "Łucja Pawlak", "Ewa Makowska",
    "Cezary Górski", "Antoni Kołodziej", "Jeremi Zakrzewski", "Wiktoria Krawczyk",
    "Konstanty Gajewski", "Natalia Malinowska", "Hanna Borkowska", "David Michalak",
    "Alex Michalski", "Milena Witkowska", "Jadwiga Sadowska", "Michał Mazur", "Noemi Sadowska",
    "Nikodem Sadowski", "Blanka Sawicka", "Bianka Krawczyk", "Marek Szymański", "Mark Nowicki",
    "Kajetan Stępień", "Florian Jankowski", "Stanisław Jankowski", "Katarzyna Walczak",
    "Ewa Nowakowska", "Stefania Kozak", "Eryk Krupa", "Florian Zając", "Helena Szulc",
    "Emil Michalak", "Oliwier Nowakowski", "Radosław Urbański", "Jeremi Włodarczyk",
    "Eliza Wasilewska", "Bruno Konieczny"
]

admin_name = dane_osob[0]                 
lekarze_names = dane_osob[1:11]           
pracownicy_names = dane_osob[11:21]       
pacjenci_names = dane_osob[21:]           

uzyte_pesele = set()
uzyte_npwz = set()
uzyte_maile = set()

def generate_unique_pesel():
    while True:
        pesel = "".join([str(random.randint(0, 9)) for _ in range(11)])
        # Obliczanie sumy kontrolnej PESEL, aby przechodził Twoją walidację
        wagi = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
        suma = sum(w * int(pesel[i]) for i, w in enumerate(wagi))
        kontrolna = (10 - (suma % 10)) % 10
        pesel = pesel[:10] + str(kontrolna)
        if pesel not in uzyte_pesele:
            uzyte_pesele.add(pesel)
            return pesel

def generate_unique_npwz():
    while True:
        npwz = "".join([str(random.randint(0, 9)) for _ in range(7)])
        if npwz not in uzyte_npwz:
            uzyte_npwz.add(npwz)
            return npwz

def fake_phone():
    return "".join([str(random.randint(0, 9)) for _ in range(9)])

def create_unique_email(imie, nazwisko):
    base_email = f"{imie.lower()}.{nazwisko.lower()}@medisync.pl"
    pl_chars = str.maketrans("ąćęłńóśźż", "acelnoszz")
    email = base_email.translate(pl_chars)
    counter = 1
    temp_email = email
    while temp_email in uzyte_maile:
        prefix, domain = email.split("@")
        temp_email = f"{prefix}{counter}@{domain}"
        counter += 1
    uzyte_maile.add(temp_email)
    return temp_email

def hash_password(password="SecureMed123!"): 
    # Bezpośrednie użycie bcrypt (bez wadliwego passlib)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def seed_database():
    session = SessionLocal()
    try:
        print("Rozpoczynam proces zasilania bazy danych Medisync (przez localhost)...")
        print("Generowanie hashy haseł zajmie kilka sekund...")
        
        # --- 1. TWORZENIE RÓL (Małymi literami, zgodnie z main.py) ---
        role_map = {}
        for r_nazwa in ["admin", "lekarz", "rejestracja", "pacjent"]:
            rola = session.query(Rola).filter_by(nazwa=r_nazwa).first()
            if not rola:
                rola = Rola(nazwa=r_nazwa)
                session.add(rola)
                session.flush()
            role_map[r_nazwa] = rola.id

        # Słownik: Specjalizacje
        nazwy_specjalizacji = ["Kardiolog", "Neurolog", "Dermatolog", "Ortopeda", "Chirurg", "Pediatra", "Okulista", "Internista"]
        obiekty_specjalizacji = []
        for nazwa in nazwy_specjalizacji:
            spec = session.query(Specjalizacja).filter_by(nazwa=nazwa).first()
            if not spec:
                spec = Specjalizacja(nazwa=nazwa)
                session.add(spec)
                session.flush()
            obiekty_specjalizacji.append(spec)

        # Słownik: Gabinety
        for num in ["101", "102", "103", "104", "105", "201", "202"]:
            gab = session.query(Gabinet).filter_by(numer=num).first()
            if not gab:
                session.add(Gabinet(numer=num, status="Dostępny"))
                
       # Słownik: Cennik (Przypisany do specjalizacji!)
        if not session.query(Cennik).first():
            cenniki = []
            # Dodajemy cennik dedykowany dla każdej wygenerowanej specjalizacji
            for spec in obiekty_specjalizacji:
                cenniki.append(
                    Cennik(
                        nazwa_uslugi=f"Konsultacja specjalistyczna - {spec.nazwa}", 
                        cena=random.choice([150.00, 200.00, 250.00, 300.00]), # Losujemy różne ceny
                        data_od=datetime.datetime.now(datetime.timezone.utc),
                        specjalizacja_id=spec.id
                    )
                )
            
            # Dodajemy jedną usługę ogólną BEZ specjalizacji (jako Twój fallback)
            cenniki.append(
                Cennik(
                    nazwa_uslugi="Konsultacja ogólna", 
                    cena=100.00, 
                    data_od=datetime.datetime.now(datetime.timezone.utc),
                    specjalizacja_id=None
                )
            )
            session.add_all(cenniki)

        # Słownik: ICD10 (Przykładowe)
        if not session.query(SlownikICD10).first():
            session.add_all([
                SlownikICD10(kod="I10", nazwa="Samoistne (pierwotne) nadciśnienie"),
                SlownikICD10(kod="J00", nazwa="Ostre zapalenie nosa i gardła"),
                SlownikICD10(kod="E11", nazwa="Cukrzyca insulinoniezależna")
            ])

        session.flush()

        # --- 2. TWORZENIE PLACÓWKI ---
        placowka = session.query(Placowka).filter_by(nr_ksiegi_rpwdl="RPWDL-000000012345").first()
        if not placowka:
            placowka = Placowka(
                nazwa="Centrum Medyczne MediSync Sp. z o.o.",
                nr_ksiegi_rpwdl="RPWDL-000000012345",
                autoryzacja_mz_do=datetime.date(2032, 12, 31),
                autoryzacja_nfz_do=datetime.date(2030, 6, 30)
            )
            session.add(placowka)
            session.flush()

        # --- 3. ADMINISTRATOR ---
        imie_adm, nazwisko_adm = admin_name.split(" ", 1)
        adm_email = create_unique_email(imie_adm, nazwisko_adm)
        if not session.query(Uzytkownik).filter_by(email=adm_email).first():
            u_admin = Uzytkownik(
                rola_id=role_map["admin"], email=adm_email,
                haslo_hash=hash_password(), profil_uzupelniony=True
            )
            session.add(u_admin)
            print(f"Dodano konto administratora: {admin_name} ({adm_email})")

        # --- 4. LEKARZE ---
        for pelne_imie in lekarze_names:
            imie, nazwisko = pelne_imie.split(" ", 1)
            email = create_unique_email(imie, nazwisko)
            if session.query(Uzytkownik).filter_by(email=email).first():
                continue
                
            u_lekarz = Uzytkownik(
                rola_id=role_map["lekarz"], email=email,
                haslo_hash=hash_password(), profil_uzupelniony=True
            )
            session.add(u_lekarz)
            session.flush()
            
            lekarz_profil = Lekarz(
                imie=imie, nazwisko=nazwisko, pesel=generate_unique_pesel(), telefon=fake_phone(),
                uzytkownik_id=u_lekarz.id, placowka_id=placowka.id, npwz=generate_unique_npwz(),
                status_npwz="Aktywny", waznosc_oc=datetime.date.today() + datetime.timedelta(days=365)
            )
            lekarz_profil.specjalizacje.append(random.choice(obiekty_specjalizacji))
            session.add(lekarz_profil)
            
        print(f"Pomyślnie dodano {len(lekarze_names)} lekarzy.")

        # --- 5. PRACOWNICY ---
        for pelne_imie in pracownicy_names:
            imie, nazwisko = pelne_imie.split(" ", 1)
            email = create_unique_email(imie, nazwisko)
            if session.query(Uzytkownik).filter_by(email=email).first():
                continue
                
            u_pracownik = Uzytkownik(
                rola_id=role_map["rejestracja"], email=email,
                haslo_hash=hash_password(), profil_uzupelniony=True
            )
            session.add(u_pracownik)
            session.flush()
            
            pracownik_profil = Pracownik(
                uzytkownik_id=u_pracownik.id, imie=imie, nazwisko=nazwisko,
                telefon=fake_phone(), pesel=generate_unique_pesel()
            )
            session.add(pracownik_profil)
        print(f"Pomyślnie dodano {len(pracownicy_names)} pracowników (rejestracja).")

        # --- 6. PACJENCI ---
        slownik_miast = ["Warszawa", "Kraków", "Łódź", "Wrocław", "Poznań", "Gdańsk"]
        slownik_ulic = ["Medyków", "Zdrowia", "Słoneczna", "Polna", "Kwiatowa"]
        
        licznik_pacjentow = 0
        for pelne_imie in pacjenci_names:
            imie, nazwisko = pelne_imie.split(" ", 1)
            email = create_unique_email(imie, nazwisko)
            if session.query(Uzytkownik).filter_by(email=email).first():
                continue
            
            adres = Adres(
                miejscowosc=random.choice(slownik_miast),
                kod_pocztowy=f"{random.randint(10, 99)}-{random.randint(100, 999)}",
                ulica=random.choice(slownik_ulic), nr_domu=str(random.randint(1, 120)),
                nr_lokalu=str(random.randint(1, 45)) if random.random() > 0.4 else None
            )
            session.add(adres)
            session.flush()
            
            u_pacjent = Uzytkownik(
                rola_id=role_map["pacjent"], email=email,
                haslo_hash=hash_password(), profil_uzupelniony=True
            )
            session.add(u_pacjent)
            session.flush()
            
            pacjent_profil = Pacjent(
                uzytkownik_id=u_pacjent.id, adres_id=adres.id, pesel=generate_unique_pesel(),
                imie=imie, nazwisko=nazwisko, telefon=fake_phone()
            )
            session.add(pacjent_profil)
            session.flush()
            
            zgoda = Zgoda(
                pacjent_id=pacjent_profil.id,
                typ_zgody="Przetwarzanie Danych Osobowych (RODO)",
                tresc_zgody="Wyrażam zgodę na przetwarzanie moich danych osobowych w celach medycznych."
            )
            session.add(zgoda)
            
            licznik_pacjentow += 1
            
        print(f"Pomyślnie dodano {licznik_pacjentow} pacjentów.")
        
        session.commit()
        print("\n[SUKCES] Baza danych MediSync została w 100% poprawnie zasilona!")
        
    except Exception as e:
        session.rollback()
        print(f"\n[BŁĄD] Wystąpił błąd: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()