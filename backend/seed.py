"""
Uruchom: docker exec medisync_backend python3 seed.py
Hasło do wszystkich kont: Test1234!
"""
from passlib.context import CryptContext
from sqlalchemy import text
from database import get_db
import random
from datetime import date, datetime, timedelta

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
HASLO = pwd.hash("Test1234!")

db = next(get_db())

try:
    # ── ROLE ──────────────────────────────────────────────────────────────────
    for rola in ["pacjent", "lekarz", "admin"]:
        db.execute(text("INSERT INTO role (nazwa) VALUES (:n) ON CONFLICT (nazwa) DO NOTHING"), {"n": rola})

    # ── SPECJALIZACJE ─────────────────────────────────────────────────────────
    specjalizacje_lista = [
        "Kardiologia", "Neurologia", "Ortopedia", "Pediatria",
        "Dermatologia", "Chirurgia ogólna", "Medycyna rodzinna", "Ginekologia",
        "Urologia", "Onkologia", "Psychiatria", "Okulistyka",
        "Laryngologia", "Endokrynologia", "Reumatologia",
    ]
    for spec in specjalizacje_lista:
        db.execute(text("INSERT INTO specjalizacje (nazwa) VALUES (:n) ON CONFLICT DO NOTHING"), {"n": spec})

    # ── PLACÓWKI ──────────────────────────────────────────────────────────────
    placowki_dane = [
        ("Przychodnia Centrum",        "W-12345", "2026-12-31", "2026-06-30"),
        ("Szpital Miejski im. Jana III", "W-67890", "2027-03-31", "2027-03-31"),
        ("Klinika MediSync",           "W-11223", "2026-09-30", "2026-09-30"),
        ("Centrum Medyczne Południe",  "W-44556", "2027-06-30", "2027-06-30"),
    ]
    for nazwa, nr, mz, nfz in placowki_dane:
        db.execute(text("""
            INSERT INTO placowki (nazwa, nr_ksiegi_rpwdl, autoryzacja_mz_do, autoryzacja_nfz_do)
            VALUES (:n, :nr, :mz, :nfz) ON CONFLICT DO NOTHING
        """), {"n": nazwa, "nr": nr, "mz": mz, "nfz": nfz})

    # ── GABINETY ──────────────────────────────────────────────────────────────
    for numer in ["101", "102", "103", "201", "202", "203", "301", "302"]:
        db.execute(text("""
            INSERT INTO gabinety (numer, status) VALUES (:n, 'Dostępny')
            ON CONFLICT (numer) DO NOTHING
        """), {"n": numer})

    # ── CENNIK ────────────────────────────────────────────────────────────────
    uslugi = [
        ("Wizyta kardiologiczna",    250.00),
        ("Wizyta neurologiczna",     220.00),
        ("Wizyta pediatryczna",      150.00),
        ("Wizyta ortopedyczna",      200.00),
        ("Wizyta dermatologiczna",   180.00),
        ("Wizyta ogólna",            120.00),
        ("Konsultacja onkologiczna", 300.00),
        ("Wizyta ginekologiczna",    200.00),
    ]
    cennik_ids = []
    for nazwa, cena in uslugi:
        row = db.execute(text("""
            INSERT INTO cennik (nazwa_uslugi, cena, data_od)
            VALUES (:n, :c, '2024-01-01') RETURNING id
        """), {"n": nazwa, "c": cena}).fetchone()
        cennik_ids.append(row.id)

    # ── SŁOWNIK ICD-10 ────────────────────────────────────────────────────────
    icd10_dane = [
        ("I10",   "Nadciśnienie pierwotne"),
        ("I21",   "Ostry zawał serca"),
        ("J06.9", "Ostre zakażenie górnych dróg oddechowych"),
        ("K29.7", "Zapalenie żołądka"),
        ("M54.5", "Ból dolnego odcinka kręgosłupa"),
        ("F32.1", "Epizod depresyjny umiarkowany"),
        ("E11",   "Cukrzyca typu 2"),
        ("J45",   "Astma oskrzelowa"),
        ("N39.0", "Zakażenie układu moczowego"),
        ("G43",   "Migrena"),
    ]
    for kod, nazwa in icd10_dane:
        db.execute(text("""
            INSERT INTO slownik_icd10 (kod, nazwa) VALUES (:k, :n) ON CONFLICT DO NOTHING
        """), {"k": kod, "n": nazwa})

    # ── ADMIN ─────────────────────────────────────────────────────────────────
    db.execute(text("""
        INSERT INTO uzytkownicy (email, haslo_hash, rola_id, profil_uzupelniony)
        VALUES ('admin@medisync.pl', :h, (SELECT id FROM role WHERE nazwa='admin'), TRUE)
        ON CONFLICT (email) DO NOTHING
    """), {"h": HASLO})
    print("✅ Admin dodany")

    # ── LEKARZE ───────────────────────────────────────────────────────────────
    lekarze_dane = [
        ("jan.nowak",        "Jan",       "Nowak",       "1234567", ["Kardiologia", "Medycyna rodzinna"]),
        ("anna.wisniewski",  "Anna",      "Wiśniewska",  "2345678", ["Neurologia"]),
        ("piotr.kowalski",   "Piotr",     "Kowalski",    "3456789", ["Ortopedia", "Chirurgia ogólna"]),
        ("maria.lewandowski","Maria",     "Lewandowska", "4567890", ["Pediatria"]),
        ("tomasz.wojcik",    "Tomasz",    "Wójcik",      "5678901", ["Dermatologia"]),
        ("katarzyna.kaminski","Katarzyna","Kamińska",    "6789012", ["Ginekologia"]),
        ("marek.kowalczyk",  "Marek",     "Kowalczyk",   "7890123", ["Urologia"]),
        ("agnieszka.zielinski","Agnieszka","Zielińska",  "8901234", ["Onkologia"]),
        ("robert.szymanski", "Robert",    "Szymański",   "9012345", ["Psychiatria"]),
        ("magdalena.wozniak","Magdalena", "Woźniak",     "0123456", ["Okulistyka"]),
        ("krzysztof.kozlowski","Krzysztof","Kozłowski",  "1122334", ["Laryngologia"]),
        ("joanna.mazur",     "Joanna",    "Mazur",       "2233445", ["Endokrynologia"]),
        ("andrzej.krawczyk", "Andrzej",   "Krawczyk",    "3344556", ["Reumatologia"]),
        ("barbara.kaczmarek","Barbara",   "Kaczmarek",   "4455667", ["Kardiologia", "Neurologia"]),
        ("michal.piotrowsk", "Michał",    "Piotrowski",  "5566778", ["Medycyna rodzinna", "Pediatria"]),
    ]

    placowki_ids = db.execute(text("SELECT id FROM placowki ORDER BY id")).fetchall()
    placowki_ids = [r.id for r in placowki_ids]

    for i, (email_prefix, imie, nazwisko, npwz, specs) in enumerate(lekarze_dane):
        email = f"{email_prefix}@medisync.pl"
        user = db.execute(text("""
            INSERT INTO uzytkownicy (email, haslo_hash, rola_id, profil_uzupelniony)
            VALUES (:e, :h, (SELECT id FROM role WHERE nazwa='lekarz'), TRUE)
            ON CONFLICT (email) DO NOTHING RETURNING id
        """), {"e": email, "h": HASLO}).fetchone()

        if user:
            placowka_id = placowki_ids[i % len(placowki_ids)]
            waznosc = date(2025 + (i % 3), (i % 12) + 1, 15)
            lekarz = db.execute(text("""
                INSERT INTO lekarze (uzytkownik_id, placowka_id, npwz, status_npwz, waznosc_oc)
                VALUES (:uid, :pid, :npwz, 'aktywny', :woc)
                RETURNING id
            """), {"uid": user.id, "pid": placowka_id, "npwz": npwz, "woc": waznosc}).fetchone()

            for spec_nazwa in specs:
                spec = db.execute(text("SELECT id FROM specjalizacje WHERE nazwa=:n"), {"n": spec_nazwa}).fetchone()
                if spec and lekarz:
                    db.execute(text("""
                        INSERT INTO lekarz_specjalizacja (lekarz_id, specjalizacja_id)
                        VALUES (:l, :s) ON CONFLICT DO NOTHING
                    """), {"l": lekarz.id, "s": spec.id})

    print("✅ Lekarze dodani (15)")

    # ── PACJENCI ──────────────────────────────────────────────────────────────
    imiona_m = ["Jan", "Piotr", "Tomasz", "Marek", "Andrzej", "Robert", "Michał",
                "Krzysztof", "Adam", "Paweł", "Łukasz", "Jakub", "Mateusz", "Kamil", "Bartosz"]
    imiona_k = ["Anna", "Maria", "Katarzyna", "Magdalena", "Agnieszka", "Barbara",
                "Joanna", "Monika", "Karolina", "Natalia", "Aleksandra", "Marta",
                "Paulina", "Dominika", "Justyna"]
    nazwiska = ["Kowalski", "Nowak", "Wiśniewski", "Wójcik", "Kowalczyk", "Kamiński",
                "Lewandowski", "Zieliński", "Szymański", "Woźniak", "Kozłowski",
                "Mazur", "Krawczyk", "Kaczmarek", "Piotrowski", "Grabowski",
                "Nowakowski", "Pawłowski", "Michalski", "Adamczyk"]
    ulice = ["Marszałkowska", "Floriańska", "Długa", "Słoneczna", "Leśna",
             "Kwiatowa", "Lipowa", "Polna", "Ogrodowa", "Szkolna"]
    miasta = [
        ("Warszawa",  "00-001"), ("Kraków",   "30-001"), ("Gdańsk",    "80-001"),
        ("Wrocław",   "50-001"), ("Poznań",   "60-001"), ("Łódź",      "90-001"),
        ("Katowice",  "40-001"), ("Lublin",   "20-001"), ("Białystok", "15-001"),
        ("Rzeszów",   "35-001"),
    ]

    for i in range(100):
        plec_m = (i % 2 == 0)
        imie = imiona_m[i % len(imiona_m)] if plec_m else imiona_k[i % len(imiona_k)]
        nazwisko = nazwiska[i % len(nazwiska)]
        suffix = "ski" if plec_m else "ska"
        if nazwisko.endswith("ski"):
            nazwisko_wl = nazwisko if plec_m else nazwisko[:-3] + "ska"
        else:
            nazwisko_wl = nazwisko

        email = f"pacjent{i+1}@test.pl"
        rok = 1950 + (i % 50)
        miesiac = (i % 12) + 1
        dzien = (i % 28) + 1
        pesel = f"{str(rok)[2:]}{miesiac:02d}{dzien:02d}{10000 + i:05d}"

        miasto, kod = miasta[i % len(miasta)]
        ulica = ulice[i % len(ulice)]

        adres = db.execute(text("""
            INSERT INTO adresy (miejscowosc, kod_pocztowy, ulica, nr_domu, nr_lokalu)
            VALUES (:m, :k, :u, :nd, :nl) RETURNING id
        """), {
            "m": miasto, "k": kod, "u": ulica,
            "nd": str((i % 50) + 1),
            "nl": str(i % 10 + 1) if i % 3 == 0 else None
        }).fetchone()

        user = db.execute(text("""
            INSERT INTO uzytkownicy (email, haslo_hash, rola_id, profil_uzupelniony)
            VALUES (:e, :h, (SELECT id FROM role WHERE nazwa='pacjent'), TRUE)
            ON CONFLICT (email) DO NOTHING RETURNING id
        """), {"e": email, "h": HASLO}).fetchone()

        if user:
            db.execute(text("""
                INSERT INTO pacjenci (uzytkownik_id, adres_id, pesel, imie, nazwisko, telefon)
                VALUES (:uid, :aid, :pesel, :imie, :nazwisko, :telefon)
            """), {
                "uid": user.id, "aid": adres.id,
                "pesel": pesel,
                "imie": imie,
                "nazwisko": nazwisko_wl,
                "telefon": f"6{i:08d}"[:9]
            })

    print("✅ Pacjenci dodani (100)")

    # ── GRAFIKI PRACY ─────────────────────────────────────────────────────────
    lekarze_ids = db.execute(text("SELECT id FROM lekarze")).fetchall()
    gabinety_ids = db.execute(text("SELECT id FROM gabinety")).fetchall()
    lekarze_ids = [r.id for r in lekarze_ids]
    gabinety_ids = [r.id for r in gabinety_ids]

    grafiki_ids = []
    base_date = datetime(2025, 6, 1, 8, 0)
    for i in range(60):
        lekarz_id = lekarze_ids[i % len(lekarze_ids)]
        gabinet_id = gabinety_ids[i % len(gabinety_ids)]
        termin_od = base_date + timedelta(days=i // 3, hours=(i % 3) * 3)
        termin_do = termin_od + timedelta(hours=3)

        grafik = db.execute(text("""
            INSERT INTO grafiki_pracy (lekarz_id, gabinet_id, termin_od, termin_do)
            VALUES (:l, :g, :od, :do) RETURNING id
        """), {"l": lekarz_id, "g": gabinet_id, "od": termin_od, "do": termin_do}).fetchone()
        grafiki_ids.append(grafik.id)

    print("✅ Grafiki pracy dodane (60)")

    # ── WIZYTY ────────────────────────────────────────────────────────────────
    pacjenci_ids = db.execute(text("SELECT id FROM pacjenci")).fetchall()
    pacjenci_ids = [r.id for r in pacjenci_ids]
    statusy = ["Zaplanowana", "Zrealizowana", "Anulowana"]

    wizyta_ids = []
    for i in range(40):
        grafik_id = grafiki_ids[i]
        pacjent_id = pacjenci_ids[i % len(pacjenci_ids)]
        cennik_id = cennik_ids[i % len(cennik_ids)]
        status = statusy[i % len(statusy)]

        wizyta = db.execute(text("""
            INSERT INTO wizyty (pacjent_id, grafik_id, cennik_id, status)
            VALUES (:p, :g, :c, :s) RETURNING id
        """), {"p": pacjent_id, "g": grafik_id, "c": cennik_id, "s": status}).fetchone()
        wizyta_ids.append(wizyta.id)

    print("✅ Wizyty dodane (40)")

    # ── DOKUMENTACJA MEDYCZNA ─────────────────────────────────────────────────
    icd_kody = [r[0] for r in icd10_dane]
    for i, wizyta_id in enumerate(wizyta_ids[:20]):
        kod = icd_kody[i % len(icd_kody)]
        db.execute(text("""
            INSERT INTO dokumentacja_medyczna (wizyta_id, kod_icd10, wywiad_lekarski)
            VALUES (:w, :k, :j)
        """), {
            "w": wizyta_id, "k": kod,
            "j": f'{{"dolegliwosci": "Opis wizyty {i+1}", "zalecenia": "Odpoczynek i nawodnienie"}}'
        })

    print("✅ Dokumentacja medyczna dodana (20)")

    # ── TRANSAKCJE ────────────────────────────────────────────────────────────
    metody = ["gotówka", "karta", "przelew"]
    statusy_tr = ["Opłacona", "Oczekująca", "Anulowana"]
    for i, wizyta_id in enumerate(wizyta_ids[:30]):
        cennik_id = cennik_ids[i % len(cennik_ids)]
        cena = db.execute(text("SELECT cena FROM cennik WHERE id=:id"), {"id": cennik_id}).fetchone()
        db.execute(text("""
            INSERT INTO transakcje (wizyta_id, kwota, metoda_platnosci, status)
            VALUES (:w, :k, :m, :s)
        """), {
            "w": wizyta_id, "k": cena.cena,
            "m": metody[i % len(metody)],
            "s": statusy_tr[i % len(statusy_tr)]
        })

    print("✅ Transakcje dodane (30)")

    # ── ZGODY PACJENTÓW ───────────────────────────────────────────────────────
    typy_zgod = [
        ("RODO", "Wyrażam zgodę na przetwarzanie danych osobowych"),
        ("marketing", "Wyrażam zgodę na kontakt marketingowy"),
        ("badania", "Wyrażam zgodę na udostępnienie danych do badań naukowych"),
    ]
    for i in range(30):
        pacjent_id = pacjenci_ids[i]
        typ, tresc = typy_zgod[i % len(typy_zgod)]
        db.execute(text("""
            INSERT INTO zgody (pacjent_id, typ_zgody, tresc_zgody)
            VALUES (:p, :t, :tr)
        """), {"p": pacjent_id, "t": typ, "tr": tresc})

    print("✅ Zgody dodane (30)")

    db.commit()

    print("\n" + "="*50)
    print("🎉 Seed zakończony pomyślnie!")
    print("="*50)
    print("🔑 Hasło do wszystkich kont: Test1234!")
    print()
    print("👤 admin@medisync.pl          — administrator")
    print("👨‍⚕️ jan.nowak@medisync.pl       — lekarz (Kardiologia)")
    print("👨‍⚕️ anna.wisniewski@medisync.pl  — lekarz (Neurologia)")
    print("👨‍⚕️ ... (15 lekarzy łącznie)")
    print("🧑 pacjent1@test.pl ... pacjent100@test.pl — pacjenci")

except Exception as e:
    db.rollback()
    print(f"❌ Błąd: {e}")
    raise
finally:
    db.close()