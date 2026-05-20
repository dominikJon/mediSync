"""
seed.py — MediSync
Uruchomienie: docker exec medisync_backend python seed.py
Idempotentny: można uruchamiać wielokrotnie bez duplikatów.
"""

from database import engine
from sqlalchemy import text
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── DANE SŁOWNIKOWE ───────────────────────────────────────────────────────────

ROLE = ["admin", "lekarz", "pracownik", "pacjent"]

SPECJALIZACJE = [
    "Kardiologia", "Neurologia", "Ortopedia", "Pediatria", "Dermatologia",
    "Ginekologia", "Okulistyka", "Psychiatria", "Endokrynologia", "Chirurgia ogólna",
]

PLACOWKI = [
    {"nazwa": "Centrum Medyczne MediSync Warszawa", "nr_ksiegi_rpwdl": "000001234"},
    {"nazwa": "Przychodnia MediSync Kraków",        "nr_ksiegi_rpwdl": "000005678"},
    {"nazwa": "Klinika MediSync Wrocław",           "nr_ksiegi_rpwdl": "000009012"},
]

GABINETY = ["101", "102", "103", "104", "105", "201", "202", "203"]

CENNIK = [
    {"nazwa_uslugi": "Wizyta ogólna",          "cena": "150.00", "data_od": "2024-01-01"},
    {"nazwa_uslugi": "Wizyta specjalistyczna",  "cena": "250.00", "data_od": "2024-01-01"},
    {"nazwa_uslugi": "Badanie EKG",            "cena": "80.00",  "data_od": "2024-01-01"},
    {"nazwa_uslugi": "Konsultacja telefoniczna","cena": "100.00", "data_od": "2024-01-01"},
    {"nazwa_uslugi": "USG jamy brzusznej",     "cena": "200.00", "data_od": "2024-01-01"},
]

# ── UŻYTKOWNICY ───────────────────────────────────────────────────────────────

ADMINOWIE = [
    {"email": "admin@medisync.pl",   "haslo": "Admin1234!"},
    {"email": "admin2@medisync.pl",  "haslo": "Admin1234!"},
]

LEKARZE = [
    {
        "email": "jan.kowalski@medisync.pl", "haslo": "Lekarz123!",
        "imie": "Jan", "nazwisko": "Kowalski",
        "pesel": "75031512345", "brak_peselu": False,
        "npwz": "1234501", "status_npwz": "aktywny", "waznosc_oc": "2026-12-31",
        "placowka_nr": 0, "specjalizacje": ["Kardiologia", "Chirurgia ogólna"],
    },
    {
        "email": "anna.nowak@medisync.pl", "haslo": "Lekarz123!",
        "imie": "Anna", "nazwisko": "Nowak",
        "pesel": "82091045678", "brak_peselu": False,
        "npwz": "1234502", "status_npwz": "aktywny", "waznosc_oc": "2027-06-30",
        "placowka_nr": 0, "specjalizacje": ["Neurologia"],
    },
    {
        "email": "piotr.wisniewski@medisync.pl", "haslo": "Lekarz123!",
        "imie": "Piotr", "nazwisko": "Wiśniewski",
        "pesel": None, "brak_peselu": True,  # lekarz zagraniczny
        "npwz": "1234503", "status_npwz": "aktywny", "waznosc_oc": "2026-09-30",
        "placowka_nr": 1, "specjalizacje": ["Ortopedia"],
    },
    {
        "email": "maria.wojcik@medisync.pl", "haslo": "Lekarz123!",
        "imie": "Maria", "nazwisko": "Wójcik",
        "pesel": "90042267890", "brak_peselu": False,
        "npwz": "1234504", "status_npwz": "aktywny", "waznosc_oc": "2027-03-31",
        "placowka_nr": 1, "specjalizacje": ["Pediatria", "Dermatologia"],
    },
    {
        "email": "tomasz.kaminski@medisync.pl", "haslo": "Lekarz123!",
        "imie": "Tomasz", "nazwisko": "Kamiński",
        "pesel": "68052312345", "brak_peselu": False,
        "npwz": "1234505", "status_npwz": "aktywny", "waznosc_oc": "2026-11-30",
        "placowka_nr": 2, "specjalizacje": ["Ginekologia", "Okulistyka"],
    },
]

PRACOWNICY = [
    {"email": "recepcja1@medisync.pl",  "haslo": "Pracownik1!", "imie": "Katarzyna", "nazwisko": "Lewandowska", "pesel": "91030512345", "telefon": "500100200"},
    {"email": "recepcja2@medisync.pl",  "haslo": "Pracownik1!", "imie": "Michał",    "nazwisko": "Zieliński",   "pesel": "85071823456", "telefon": "500100201"},
    {"email": "recepcja3@medisync.pl",  "haslo": "Pracownik1!", "imie": "Agnieszka", "nazwisko": "Szymańska",   "pesel": "93112534567", "telefon": "500100202"},
    {"email": "recepcja4@medisync.pl",  "haslo": "Pracownik1!", "imie": "Krzysztof", "nazwisko": "Woźniak",     "pesel": "78040145678", "telefon": "500100203"},
    {"email": "recepcja5@medisync.pl",  "haslo": "Pracownik1!", "imie": "Magdalena", "nazwisko": "Dąbrowska",   "pesel": "95061856789", "telefon": "500100204"},
]

PACJENCI = [
    {"email": "adam.adamczyk@gmail.com",      "imie": "Adam",      "nazwisko": "Adamczyk",      "pesel": "80010112345", "telefon": "600200300", "miejscowosc": "Warszawa",  "kod": "00-001", "ulica": "Marszałkowska",  "nr_domu": "10"},
    {"email": "barbara.baranowska@gmail.com", "imie": "Barbara",   "nazwisko": "Baranowska",    "pesel": "75052334521", "telefon": "600200301", "miejscowosc": "Kraków",    "kod": "30-001", "ulica": "Floriańska",     "nr_domu": "5"},
    {"email": "cezary.chmielewski@gmail.com", "imie": "Cezary",    "nazwisko": "Chmielewski",   "pesel": "92030378965", "telefon": "600200302", "miejscowosc": "Wrocław",   "kod": "50-001", "ulica": "Świdnicka",      "nr_domu": "22"},
    {"email": "dorota.dabrowska@gmail.com",   "imie": "Dorota",    "nazwisko": "Dąbrowska",     "pesel": "88121445632", "telefon": "600200303", "miejscowosc": "Gdańsk",    "kod": "80-001", "ulica": "Długa",          "nr_domu": "3"},
    {"email": "edward.elzbieta@gmail.com",    "imie": "Edward",    "nazwisko": "Elżbietowski",  "pesel": "71040556987", "telefon": "600200304", "miejscowosc": "Poznań",    "kod": "60-001", "ulica": "Święty Marcin",  "nr_domu": "15"},
    {"email": "felicja.filipiak@gmail.com",   "imie": "Felicja",   "nazwisko": "Filipiak",      "pesel": "95080167423", "telefon": "600200305", "miejscowosc": "Łódź",      "kod": "90-001", "ulica": "Piotrkowska",    "nr_domu": "100"},
    {"email": "grzegorz.grabowski@gmail.com", "imie": "Grzegorz",  "nazwisko": "Grabowski",     "pesel": "83061278654", "telefon": "600200306", "miejscowosc": "Szczecin",  "kod": "70-001", "ulica": "Bohaterów",      "nr_domu": "7"},
    {"email": "halina.hajduk@gmail.com",      "imie": "Halina",    "nazwisko": "Hajduk",        "pesel": "69032389012", "telefon": "600200307", "miejscowosc": "Lublin",    "kod": "20-001", "ulica": "Krakowskie",     "nr_domu": "2"},
    {"email": "igor.iwanowski@gmail.com",     "imie": "Igor",      "nazwisko": "Iwanowski",     "pesel": "97051490345", "telefon": "600200308", "miejscowosc": "Katowice",  "kod": "40-001", "ulica": "Mariacka",       "nr_domu": "8"},
    {"email": "jadwiga.jankowska@gmail.com",  "imie": "Jadwiga",   "nazwisko": "Jankowska",     "pesel": "73091501678", "telefon": "600200309", "miejscowosc": "Białystok", "kod": "15-001", "ulica": "Lipowa",         "nr_domu": "12"},
    {"email": "karol.kaczmarek@gmail.com",    "imie": "Karol",     "nazwisko": "Kaczmarek",     "pesel": "86112612901", "telefon": "600200310", "miejscowosc": "Warszawa",  "kod": "02-001", "ulica": "Puławska",       "nr_domu": "45"},
    {"email": "lidia.lewandowska@gmail.com",  "imie": "Lidia",     "nazwisko": "Lewandowska",   "pesel": "91072723234", "telefon": "600200311", "miejscowosc": "Kraków",    "kod": "31-001", "ulica": "Grodzka",        "nr_domu": "9"},
    {"email": "marek.majewski@gmail.com",     "imie": "Marek",     "nazwisko": "Majewski",      "pesel": "78041834567", "telefon": "600200312", "miejscowosc": "Wrocław",   "kod": "51-001", "ulica": "Ruska",          "nr_domu": "17"},
    {"email": "natalia.nowacka@gmail.com",    "imie": "Natalia",   "nazwisko": "Nowacka",       "pesel": "94052945890", "telefon": "600200313", "miejscowosc": "Gdynia",    "kod": "81-001", "ulica": "Świętojańska",   "nr_domu": "34"},
    {"email": "oskar.olszewski@gmail.com",    "imie": "Oskar",     "nazwisko": "Olszewski",     "pesel": "82091056123", "telefon": "600200314", "miejscowosc": "Poznań",    "kod": "61-001", "ulica": "Półwiejska",     "nr_domu": "6"},
    {"email": "paulina.pawlak@gmail.com",     "imie": "Paulina",   "nazwisko": "Pawlak",        "pesel": "96030167456", "telefon": "600200315", "miejscowosc": "Łódź",      "kod": "91-001", "ulica": "Sienkiewicza",   "nr_domu": "11"},
    {"email": "rafal.rojek@gmail.com",        "imie": "Rafał",     "nazwisko": "Rojek",         "pesel": "74060278789", "telefon": "600200316", "miejscowosc": "Warszawa",  "kod": "03-001", "ulica": "Nowy Świat",     "nr_domu": "20"},
    {"email": "sylwia.sobieraj@gmail.com",    "imie": "Sylwia",    "nazwisko": "Sobieraj",      "pesel": "89042389012", "telefon": "600200317", "miejscowosc": "Kraków",    "kod": "32-001", "ulica": "Karmelicka",     "nr_domu": "4"},
    {"email": "tadeusz.tomaszewski@gmail.com","imie": "Tadeusz",   "nazwisko": "Tomaszewski",   "pesel": "67071490345", "telefon": "600200318", "miejscowosc": "Gdańsk",    "kod": "81-002", "ulica": "Wrzeszcz",       "nr_domu": "30"},
    {"email": "urszula.urbanska@gmail.com",   "imie": "Urszula",   "nazwisko": "Urbańska",      "pesel": "93111501678", "telefon": "600200319", "miejscowosc": "Wrocław",   "kod": "52-001", "ulica": "Legnicka",       "nr_domu": "55"},
    {"email": "waldemar.wieczorek@gmail.com", "imie": "Waldemar",  "nazwisko": "Wieczorek",     "pesel": "80031612901", "telefon": "600200320", "miejscowosc": "Lublin",    "kod": "21-001", "ulica": "Narutowicza",    "nr_domu": "18"},
    {"email": "weronika.wisz@gmail.com",      "imie": "Weronika",  "nazwisko": "Wisz",          "pesel": "97060723234", "telefon": "600200321", "miejscowosc": "Szczecin",  "kod": "71-001", "ulica": "Rayskiego",      "nr_domu": "3"},
    {"email": "xavier.xinski@gmail.com",      "imie": "Ksawery",   "nazwisko": "Ksiński",       "pesel": "85042834567", "telefon": "600200322", "miejscowosc": "Katowice",  "kod": "41-001", "ulica": "3 Maja",         "nr_domu": "14"},
    {"email": "yvonne.ybrowska@gmail.com",    "imie": "Iwona",     "nazwisko": "Ybrowska",      "pesel": "91071945890", "telefon": "600200323", "miejscowosc": "Białystok", "kod": "16-001", "ulica": "Rynek Kościuszki","nr_domu": "1"},
    {"email": "zbigniew.zawadzki@gmail.com",  "imie": "Zbigniew",  "nazwisko": "Zawadzki",      "pesel": "76040056123", "telefon": "600200324", "miejscowosc": "Poznań",    "kod": "62-001", "ulica": "Dąbrowskiego",   "nr_domu": "9"},
    {"email": "alicja.antoniak@gmail.com",    "imie": "Alicja",    "nazwisko": "Antoniak",      "pesel": "88121167456", "telefon": "600200325", "miejscowosc": "Warszawa",  "kod": "04-001", "ulica": "Mokotowska",     "nr_domu": "21"},
    {"email": "bartosz.brzezinski@gmail.com", "imie": "Bartosz",   "nazwisko": "Brzeziński",    "pesel": "93052278789", "telefon": "600200326", "miejscowosc": "Kraków",    "kod": "33-001", "ulica": "Długa",          "nr_domu": "7"},
    {"email": "celina.czajka@gmail.com",      "imie": "Celina",    "nazwisko": "Czajka",        "pesel": "71081389012", "telefon": "600200327", "miejscowosc": "Gdańsk",    "kod": "82-001", "ulica": "Oliwska",        "nr_domu": "16"},
    {"email": "damian.dabrowski@gmail.com",   "imie": "Damian",    "nazwisko": "Dąbrowski",     "pesel": "96010490345", "telefon": "600200328", "miejscowosc": "Wrocław",   "kod": "53-001", "ulica": "Piłsudskiego",   "nr_domu": "38"},
    {"email": "elzbieta.erikson@gmail.com",   "imie": "Elżbieta",  "nazwisko": "Erikson",       "pesel": "84031501678", "telefon": "600200329", "miejscowosc": "Łódź",      "kod": "92-001", "ulica": "Żeromskiego",    "nr_domu": "5"},
    {"email": "filip.frankowski@gmail.com",   "imie": "Filip",     "nazwisko": "Frankowski",    "pesel": "79072612901", "telefon": "600200330", "miejscowosc": "Katowice",  "kod": "42-001", "ulica": "Korfantego",     "nr_domu": "29"},
    {"email": "gabriela.gorska@gmail.com",    "imie": "Gabriela",  "nazwisko": "Górska",        "pesel": "94041723234", "telefon": "600200331", "miejscowosc": "Lublin",    "kod": "22-001", "ulica": "Zamojska",       "nr_domu": "11"},
    {"email": "henryk.holowka@gmail.com",     "imie": "Henryk",    "nazwisko": "Hołówka",       "pesel": "68112834567", "telefon": "600200332", "miejscowosc": "Białystok", "kod": "17-001", "ulica": "Mickiewicza",    "nr_domu": "6"},
    {"email": "irena.iwanska@gmail.com",      "imie": "Irena",     "nazwisko": "Iwańska",       "pesel": "82030945890", "telefon": "600200333", "miejscowosc": "Szczecin",  "kod": "72-001", "ulica": "Wyszyńskiego",   "nr_domu": "43"},
    {"email": "jakub.jablonski@gmail.com",    "imie": "Jakub",     "nazwisko": "Jabłoński",     "pesel": "97091056123", "telefon": "600200334", "miejscowosc": "Gdynia",    "kod": "82-002", "ulica": "Chylońska",      "nr_domu": "2"},
    {"email": "kamila.kowalczyk@gmail.com",   "imie": "Kamila",    "nazwisko": "Kowalczyk",     "pesel": "91061167456", "telefon": "600200335", "miejscowosc": "Poznań",    "kod": "63-001", "ulica": "Roosevelta",     "nr_domu": "19"},
    {"email": "leon.lewicki@gmail.com",       "imie": "Leon",      "nazwisko": "Lewicki",       "pesel": "75042278789", "telefon": "600200336", "miejscowosc": "Warszawa",  "kod": "05-001", "ulica": "Chłodna",        "nr_domu": "32"},
    {"email": "marta.michalska@gmail.com",    "imie": "Marta",     "nazwisko": "Michalska",     "pesel": "88091389012", "telefon": "600200337", "miejscowosc": "Kraków",    "kod": "34-001", "ulica": "Krupnicza",      "nr_domu": "8"},
    {"email": "nikodem.nowicki@gmail.com",    "imie": "Nikodem",   "nazwisko": "Nowicki",       "pesel": "93050490345", "telefon": "600200338", "miejscowosc": "Wrocław",   "kod": "54-001", "ulica": "Wysoka",         "nr_domu": "13"},
    {"email": "oliwia.ostrowska@gmail.com",   "imie": "Oliwia",    "nazwisko": "Ostrowska",     "pesel": "00261501678", "telefon": "600200339", "miejscowosc": "Gdańsk",    "kod": "83-001", "ulica": "Sopocka",        "nr_domu": "27"},
    {"email": "pawel.piotrowski@gmail.com",   "imie": "Paweł",     "nazwisko": "Piotrowski",    "pesel": "82071612901", "telefon": "600200340", "miejscowosc": "Łódź",      "kod": "93-001", "ulica": "Wojska Polskiego","nr_domu": "4"},
    {"email": "renata.rogalska@gmail.com",    "imie": "Renata",    "nazwisko": "Rogalska",      "pesel": "77031723234", "telefon": "600200341", "miejscowosc": "Katowice",  "kod": "43-001", "ulica": "Bytkowska",      "nr_domu": "22"},
    {"email": "stanislaw.szymanski@gmail.com","imie": "Stanisław", "nazwisko": "Szymański",     "pesel": "65091834567", "telefon": "600200342", "miejscowosc": "Lublin",    "kod": "23-001", "ulica": "Chopina",        "nr_domu": "17"},
    {"email": "teresa.twardowska@gmail.com",  "imie": "Teresa",    "nazwisko": "Twardowska",    "pesel": "90040945890", "telefon": "600200343", "miejscowosc": "Białystok", "kod": "18-001", "ulica": "Świętojańska",   "nr_domu": "9"},
    {"email": "ulryk.urbaniak@gmail.com",     "imie": "Ulryk",     "nazwisko": "Urbaniak",      "pesel": "84111056123", "telefon": "600200344", "miejscowosc": "Szczecin",  "kod": "73-001", "ulica": "Kolumba",        "nr_domu": "31"},
    {"email": "violetta.voss@gmail.com",      "imie": "Violetta",  "nazwisko": "Voss",          "pesel": "92051167456", "telefon": "600200345", "miejscowosc": "Gdynia",    "kod": "83-002", "ulica": "Armii Krajowej", "nr_domu": "44"},
    {"email": "wojciech.witek@gmail.com",     "imie": "Wojciech",  "nazwisko": "Witek",         "pesel": "78122278789", "telefon": "600200346", "miejscowosc": "Poznań",    "kod": "64-001", "ulica": "Bukowska",       "nr_domu": "10"},
    {"email": "zuzanna.zielinska@gmail.com",  "imie": "Zuzanna",   "nazwisko": "Zielińska",     "pesel": "97030389012", "telefon": "600200347", "miejscowosc": "Warszawa",  "kod": "06-001", "ulica": "Andersa",        "nr_domu": "3"},
    {"email": "andrzej.antczak@gmail.com",    "imie": "Andrzej",   "nazwisko": "Antczak",       "pesel": "69060490345", "telefon": "600200348", "miejscowosc": "Kraków",    "kod": "35-001", "ulica": "Rakowicka",      "nr_domu": "26"},
]


# ── SEED ─────────────────────────────────────────────────────────────────────

def seed():
    with engine.connect() as conn:

        print("⏳ Seeding MediSync...")

        # 1. Role
        print("  → Role...")
        for nazwa in ROLE:
            istnieje = conn.execute(
                text("SELECT id FROM role WHERE nazwa = :nazwa"), {"nazwa": nazwa}
            ).fetchone()
            if not istnieje:
                conn.execute(
                    text("INSERT INTO role (nazwa) VALUES (:nazwa)"), {"nazwa": nazwa}
                )
        conn.commit()

        # 2. Specjalizacje
        print("  → Specjalizacje...")
        for nazwa in SPECJALIZACJE:
            istnieje = conn.execute(
                text("SELECT id FROM specjalizacje WHERE nazwa = :nazwa"), {"nazwa": nazwa}
            ).fetchone()
            if not istnieje:
                conn.execute(
                    text("INSERT INTO specjalizacje (nazwa) VALUES (:nazwa)"), {"nazwa": nazwa}
                )
        conn.commit()

        # 3. Placówki
        print("  → Placówki...")
        for p in PLACOWKI:
            istnieje = conn.execute(
                text("SELECT id FROM placowki WHERE nr_ksiegi_rpwdl = :nr"),
                {"nr": p["nr_ksiegi_rpwdl"]}
            ).fetchone()
            if not istnieje:
                conn.execute(text("""
                    INSERT INTO placowki (nazwa, nr_ksiegi_rpwdl)
                    VALUES (:nazwa, :nr)
                """), {"nazwa": p["nazwa"], "nr": p["nr_ksiegi_rpwdl"]})
        conn.commit()

        # 4. Gabinety
        print("  → Gabinety...")
        for numer in GABINETY:
            istnieje = conn.execute(
                text("SELECT id FROM gabinety WHERE numer = :numer"), {"numer": numer}
            ).fetchone()
            if not istnieje:
                conn.execute(
                    text("INSERT INTO gabinety (numer, status) VALUES (:numer, 'Dostępny')"),
                    {"numer": numer}
                )
        conn.commit()

        # 5. Cennik
        print("  → Cennik...")
        for c in CENNIK:
            istnieje = conn.execute(
                text("SELECT id FROM cennik WHERE nazwa_uslugi = :nazwa"),
                {"nazwa": c["nazwa_uslugi"]}
            ).fetchone()
            if not istnieje:
                conn.execute(text("""
                    INSERT INTO cennik (nazwa_uslugi, cena, data_od)
                    VALUES (:nazwa, :cena, :data_od)
                """), {"nazwa": c["nazwa_uslugi"], "cena": c["cena"], "data_od": c["data_od"]})
        conn.commit()

        # 6. Adminowie
        print("  → Adminowie...")
        rola_admin = conn.execute(
            text("SELECT id FROM role WHERE nazwa = 'admin'")
        ).fetchone()

        for a in ADMINOWIE:
            istnieje = conn.execute(
                text("SELECT id FROM uzytkownicy WHERE email = :email"), {"email": a["email"]}
            ).fetchone()
            if not istnieje:
                conn.execute(text("""
                    INSERT INTO uzytkownicy (email, haslo_hash, rola_id, profil_uzupelniony)
                    VALUES (:email, :hash, :rola_id, TRUE)
                """), {
                    "email": a["email"],
                    "hash": pwd_context.hash(a["haslo"]),
                    "rola_id": rola_admin.id,
                })
        conn.commit()

        # 7. Lekarze
        print("  → Lekarze...")
        rola_lekarz = conn.execute(
            text("SELECT id FROM role WHERE nazwa = 'lekarz'")
        ).fetchone()

        placowki_db = conn.execute(
            text("SELECT id FROM placowki ORDER BY id")
        ).fetchall()

        for l in LEKARZE:
            istnieje = conn.execute(
                text("SELECT id FROM uzytkownicy WHERE email = :email"), {"email": l["email"]}
            ).fetchone()
            if istnieje:
                continue

            nowy_user = conn.execute(text("""
                INSERT INTO uzytkownicy (email, haslo_hash, rola_id, profil_uzupelniony)
                VALUES (:email, :hash, :rola_id, TRUE)
                RETURNING id
            """), {
                "email": l["email"],
                "hash": pwd_context.hash(l["haslo"]),
                "rola_id": rola_lekarz.id,
            }).fetchone()

            placowka_id = placowki_db[l["placowka_nr"]].id

            nowy_lekarz = conn.execute(text("""
                INSERT INTO lekarze
                    (uzytkownik_id, placowka_id, imie, nazwisko, pesel,
                     npwz, status_npwz, waznosc_oc)
                VALUES
                    (:uid, :pid, :imie, :nazwisko, :pesel,
                     :npwz, :status_npwz, :waznosc_oc)
                RETURNING id
            """), {
                "uid": nowy_user.id,
                "pid": placowka_id,
                "imie": l["imie"],
                "nazwisko": l["nazwisko"],
                "pesel": l["pesel"] if not l["brak_peselu"] else None,
                "npwz": l["npwz"],
                "status_npwz": l["status_npwz"],
                "waznosc_oc": l["waznosc_oc"],
            }).fetchone()

            for spec_nazwa in l["specjalizacje"]:
                spec = conn.execute(
                    text("SELECT id FROM specjalizacje WHERE nazwa = :nazwa"),
                    {"nazwa": spec_nazwa}
                ).fetchone()
                if spec:
                    conn.execute(text("""
                        INSERT INTO lekarz_specjalizacja (lekarz_id, specjalizacja_id)
                        VALUES (:lid, :sid)
                        ON CONFLICT DO NOTHING
                    """), {"lid": nowy_lekarz.id, "sid": spec.id})

        conn.commit()

        # 8. Pracownicy
        print("  → Pracownicy...")
        rola_pracownik = conn.execute(
            text("SELECT id FROM role WHERE nazwa = 'pracownik'")
        ).fetchone()

        for p in PRACOWNICY:
            istnieje = conn.execute(
                text("SELECT id FROM uzytkownicy WHERE email = :email"), {"email": p["email"]}
            ).fetchone()
            if istnieje:
                continue

            nowy_user = conn.execute(text("""
                INSERT INTO uzytkownicy (email, haslo_hash, rola_id, profil_uzupelniony)
                VALUES (:email, :hash, :rola_id, TRUE)
                RETURNING id
            """), {
                "email": p["email"],
                "hash": pwd_context.hash(p["haslo"]),
                "rola_id": rola_pracownik.id,
            }).fetchone()

            conn.execute(text("""
                INSERT INTO pracownicy (uzytkownik_id, imie, nazwisko, pesel, telefon)
                VALUES (:uid, :imie, :nazwisko, :pesel, :telefon)
            """), {
                "uid": nowy_user.id,
                "imie": p["imie"],
                "nazwisko": p["nazwisko"],
                "pesel": p["pesel"],
                "telefon": p["telefon"],
            })

        conn.commit()

        # 9. Pacjenci
        print("  → Pacjenci...")
        rola_pacjent = conn.execute(
            text("SELECT id FROM role WHERE nazwa = 'pacjent'")
        ).fetchone()

        for p in PACJENCI:
            istnieje = conn.execute(
                text("SELECT id FROM uzytkownicy WHERE email = :email"), {"email": p["email"]}
            ).fetchone()
            if istnieje:
                continue

            nowy_user = conn.execute(text("""
                INSERT INTO uzytkownicy (email, haslo_hash, rola_id, profil_uzupelniony)
                VALUES (:email, :hash, :rola_id, TRUE)
                RETURNING id
            """), {
                "email": p["email"],
                "hash": pwd_context.hash("Pacjent123!"),
                "rola_id": rola_pacjent.id,
            }).fetchone()

            nowy_adres = conn.execute(text("""
                INSERT INTO adresy (miejscowosc, kod_pocztowy, ulica, nr_domu)
                VALUES (:miejscowosc, :kod, :ulica, :nr_domu)
                RETURNING id
            """), {
                "miejscowosc": p["miejscowosc"],
                "kod": p["kod"],
                "ulica": p["ulica"],
                "nr_domu": p["nr_domu"],
            }).fetchone()

            conn.execute(text("""
                INSERT INTO pacjenci
                    (uzytkownik_id, adres_id, pesel, imie, nazwisko, telefon)
                VALUES
                    (:uid, :adres_id, :pesel, :imie, :nazwisko, :telefon)
            """), {
                "uid": nowy_user.id,
                "adres_id": nowy_adres.id,
                "pesel": p["pesel"],
                "imie": p["imie"],
                "nazwisko": p["nazwisko"],
                "telefon": p["telefon"],
            })

        conn.commit()

        print("\n✅ Seed zakończony pomyślnie!")
        print("   Dodano: 2 adminów, 5 lekarzy, 5 pracowników, 50 pacjentów")
        print("   Słowniki: role, specjalizacje, placówki, gabinety, cennik")
        print("\n📋 Dane logowania:")
        print("   Admin:      admin@medisync.pl      / Admin1234!")
        print("   Lekarz:     jan.kowalski@medisync.pl / Lekarz123!")
        print("   Pracownik:  recepcja1@medisync.pl  / Pracownik1!")
        print("   Pacjent:    adam.adamczyk@gmail.com / Pacjent123!")


if __name__ == "__main__":
    seed()