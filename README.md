# 🏥 MediSync – System Zarządzania Przychodnią Medyczną

MediSync to aplikacja webowa wspierająca zarządzanie przychodnią medyczną. Umożliwia rejestrację wizyt, zarządzanie harmonogramami lekarzy, prowadzenie Elektronicznej Dokumentacji Medycznej (EDM), obsługę pacjentów oraz automatyczną komunikację e-mailową – wszystko w jednym, spójnym systemie.

---

## 🛠️ Technologie

| Warstwa | Technologia |
|---|---|
| **Frontend** | Vue.js 3, TypeScript, Vite, Pinia, Vue Router |
| **Backend** | FastAPI (Python 3.12), SQLAlchemy, Pydantic |
| **Baza danych** | PostgreSQL 18 |
| **Serwer pocztowy** | Mailpit (dev SMTP) |
| **Konteneryzacja** | Docker, Docker Compose |
| **Autoryzacja** | JWT (JSON Web Tokens), bcrypt |

---

## 👥 Role użytkowników

System obsługuje cztery role z różnymi uprawnieniami:

| Rola | Możliwości |
|---|---|
| **Pacjent** | Rejestracja, rezerwacja i odwoływanie wizyt (do 24h przed terminem), podgląd historii wizyt z EDM, cennik |
| **Lekarz** | Podgląd kalendarza wizyt, wypełnianie EDM (wywiad lekarski + kod ICD-10), historia zakończonych wizyt, wyszukiwanie kartoteki pacjenta |
| **Rejestracja** | Zarządzanie gabinetami i grafikami pracy, umawianie wizyt w imieniu pacjentów, podgląd harmonogramu dnia |
| **Admin** | Pełny dostęp + zarządzanie użytkownikami (dodawanie lekarzy, pracowników), panel statystyk, raporty wizyt |

---

## 🚀 Uruchomienie projektu

### Wymagania wstępne

- [Docker](https://docs.docker.com/get-docker/) i Docker Compose
- [Node.js](https://nodejs.org/) (v18+) oraz npm

---

### 1. Konfiguracja zmiennych środowiskowych
Minimalny wymagany `.env`:

```env
DB_PASSWORD=medisync_pass
SECRET_KEY=twoj-dlugi-losowy-klucz-min-32-znaki
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_SERVER=mailpit
MAIL_PORT=1025
MAIL_FROM=noreply@medisync.pl
SWAGGER_USERNAME=admin
SWAGGER_PASSWORD=MediSync2026!
ENV=development
```

> ⚠️ `SECRET_KEY` musi być długim, losowym ciągiem. Służy do podpisywania tokenów JWT. Nigdy nie commituj pliku `.env` do repozytorium.

---

### 2. Uruchomienie backendu i usług

```bash
docker compose up --build -d
```

Uruchamia trzy kontenery: `medisync_backend` (FastAPI), `medisync_db` (PostgreSQL), `mailpit` (SMTP).

---

### 3. Inicjalizacja bazy danych

Po pierwszym uruchomieniu kontenerów:

```bash
# Tworzy tabele i triggery
docker compose exec backend python init_db.py

# Ładuje dane testowe (lekarzy, pacjentów, grafiki, wizyty)
docker compose exec backend python seed.py
```

> **Reset bazy do stanu początkowego:**
> ```bash
> docker compose exec backend python reset_db.py
> ```

---

### 4. Uruchomienie frontendu

```bash
cd frontend
npm install
npm run dev
```

---

## 🌐 Dostępne usługi

| Usługa | Adres |
|---|---|
| 🖥️ **Aplikacja webowa** | http://localhost:5173 |
| ⚙️ **API + Swagger UI** | http://localhost:8000/docs |
| 🗄️ **Baza danych PostgreSQL** | `localhost:5432` |
| 📧 **Podgląd e-maili (Mailpit)** | http://localhost:8025 |

> **Swagger UI** jest chroniony HTTP Basic Auth (dane z `.env`: `SWAGGER_USERNAME` / `SWAGGER_PASSWORD`). Dostępny tylko gdy `ENV=development`.

---

## 📂 Struktura projektu

```
MediSync/
├── backend/
│   ├── models/
│   │   ├── models.py         # Definicje tabel ORM (SQLAlchemy) + triggery audytowe
│   │   └── schemas.py        # Schematy Pydantic — walidacja danych wejściowych
│   ├── routers/
│   │   ├── auth.py           # Logowanie, rejestracja, reset hasła
│   │   ├── admin.py          # Panel admina, użytkownicy, raporty
│   │   ├── gabinety.py       # CRUD gabinetów + kaskadowe odwoływanie wizyt
│   │   ├── grafiki.py        # Grafiki pracy, pulpit recepcji
│   │   ├── wizyty.py         # Rezerwacje, wolne sloty, odwoływanie (z emailami)
│   │   ├── lekarz.py         # Panel lekarza, EDM, słownik ICD-10
│   │   ├── pacjent.py        # Profil i historia pacjenta
│   │   └── raporty.py        # Raporty dla admina, cennik
│   ├── database.py           # Połączenie z PostgreSQL (SQLAlchemy engine + get_db)
│   ├── dependencies.py       # JWT, bcrypt, FastMail, helpery ról (tylko_admin itp.)
│   ├── main.py               # Konfiguracja FastAPI, CORS, Swagger auth, routery
│   ├── init_db.py            # Tworzenie tabel i triggerów
│   ├── seed.py               # Dane testowe
│   └── reset_db.py           # Reset bazy
├── frontend/
│   └── src/
│       ├── components/
│       │   └── home/         # Komponenty pulpitu per rola (PacjentHome, LekarzHome itd.)
│       ├── router/
│       │   └── index.ts      # Trasy + guardy nawigacji (auth, profil, role)
│       ├── stores/
│       │   └── auth.ts       # Pinia store — token JWT, dane użytkownika
│       └── views/            # Widoki aplikacji
├── docker-compose.yml
└── .env.example
```

---

## 🔐 Bezpieczeństwo

- **JWT** — tokeny 8-godzinne, podpisane HMAC-SHA256, zawierają rolę użytkownika
- **bcrypt** — hashowanie haseł z salt (odporne na ataki słownikowe i rainbow tables)
- **Parametryzowane zapytania SQL** — ochrona przed SQL Injection we wszystkich endpointach
- **Ochrona przed overbookingiem** — `FOR UPDATE NOWAIT` (blokada wiersza) + `UNIQUE CONSTRAINT` na `grafik_id`
- **CORS** — dozwolony tylko `http://localhost:5173`
- **Swagger Basic Auth** — dokumentacja API chroniona hasłem, wyłączona na produkcji

---

## 📧 System powiadomień e-mail

Aplikacja wysyła automatyczne powiadomienia e-mail w następujących sytuacjach:

- ✅ Odwołanie wizyty przez pacjenta → email do lekarza i recepcji
- ✅ Odwołanie wizyty przez lekarza → email do pacjenta i recepcji
- ✅ Odwołanie wizyty przez recepcję → email do pacjenta i lekarza
- ✅ Zmiana statusu gabinetu na Niedostępny → kaskadowe odwołanie wizyt + emaile do wszystkich stron
- ✅ Reset hasła → link z tokenem ważnym 15 minut

W środowisku deweloperskim wszystkie emaile przechwytuje **Mailpit** dostępny pod http://localhost:8025.

---

## 🗄️ Kluczowe elementy bazy danych

- **Trigger audytowy** — każda zmiana w tabeli `wizyty` (INSERT/UPDATE/DELETE) jest rejestrowana w `logi_audytowe` z pełnym JSON starego i nowego stanu wiersza
- **Auto-zamykanie wizyt** — wizyty bez EDM po >24h od terminu automatycznie otrzymują status `Nieobecność`
- **JSONB** — wywiad lekarski przechowywany jako binary JSON (indeksowalny, elastyczny schemat)
- **Słownik ICD-10** — ~180 kodów chorób z wyszukiwaniem pełnotekstowym i sortowaniem po prefiksie kodu

---

## 📖 Dokumentacja API

Interaktywna dokumentacja Swagger UI jest dostępna pod:

**http://localhost:8000/docs** *(wymaga Basic Auth z `.env`)*

Zawiera wszystkie endpointy z opisami parametrów, przykładowymi requestami i responsami. Do testowania endpointów w Swagger użyj przycisku **Authorize** i podaj dane swojego konta.
