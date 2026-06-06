from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal
from datetime import date
import re

# helpery walidacyjne
def waliduj_pesel(pesel: str) -> bool:
    if not re.match(r"^\d{11}$", pesel):
        return False
    wagi = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
    suma = sum(w * int(pesel[i]) for i, w in enumerate(wagi))
    kontrolna = (10 - (suma % 10)) % 10
    return kontrolna == int(pesel[10])

REGEX_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
REGEX_LITERY_PL = re.compile(r"^[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ\s-]+$")
REGEX_TELEFON = re.compile(r"^(\+48)?\d{9}$")
REGEX_KOD_POCZTOWY = re.compile(r"^\d{2}-\d{3}$")
REGEX_NR_DOMU = re.compile(r"^[a-zA-Z0-9\-\/]+$")
REGEX_ZNAK_SPECJALNY = re.compile(r"[!@#$%^&*(),.?\":{}|<>_\-]")

# modele z walidacja
class LoginRequest(BaseModel):
    email: str
    haslo: str

    @field_validator("email")
    @classmethod
    def waliduj_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not REGEX_EMAIL.match(v): raise ValueError("Nieprawidłowy format adresu email")
        return v

    @field_validator("haslo")
    @classmethod
    def waliduj_haslo_niepuste(cls, v: str) -> str:
        if not v: raise ValueError("Hasło jest wymagane")
        return v

class RejestracjaRequest(BaseModel):
    email: str
    haslo: str

    @field_validator("email")
    @classmethod
    def waliduj_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not REGEX_EMAIL.match(v): raise ValueError("Nieprawidłowy format adresu email")
        return v

    @field_validator("haslo")
    @classmethod
    def waliduj_haslo(cls, v: str) -> str:
        if len(v) < 12: raise ValueError("Hasło musi mieć co najmniej 12 znaków")
        if not re.search(r"[A-Z]", v): raise ValueError("Hasło musi zawierać co najmniej jedną wielką literę")
        if not re.search(r"[a-z]", v): raise ValueError("Hasło musi zawierać co najmniej jedną małą literę")
        if not re.search(r"\d", v): raise ValueError("Hasło musi zawierać co najmniej jedną cyfrę")
        if not REGEX_ZNAK_SPECJALNY.search(v): raise ValueError("Hasło musi zawierać co najmniej jeden znak specjalny")
        return v

class ResetHaslaRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def waliduj_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not REGEX_EMAIL.match(v): raise ValueError("Nieprawidłowy format adresu email")
        return v

class NoweHasloRequest(BaseModel):
    token: str
    nowe_haslo: str

    @field_validator("nowe_haslo")
    @classmethod
    def waliduj_haslo(cls, v: str) -> str:
        if len(v) < 12: raise ValueError("Hasło musi mieć co najmniej 12 znaków")
        if not re.search(r"[A-Z]", v): raise ValueError("Hasło musi zawierać wielką literę")
        if not re.search(r"[a-z]", v): raise ValueError("Hasło musi zawierać małą literę")
        if not re.search(r"\d", v): raise ValueError("Hasło musi zawierać cyfrę")
        if not REGEX_ZNAK_SPECJALNY.search(v): raise ValueError("Hasło musi zawierać znak specjalny")
        return v

class KartotekaRequest(BaseModel):
    uzytkownik_id: int
    imie: str
    nazwisko: str
    pesel: str
    telefon: str
    miejscowosc: str
    kod_pocztowy: str
    ulica: Optional[str] = None
    nr_domu: str
    nr_lokalu: Optional[str] = None
    brak_ulicy: bool = False

    @field_validator("imie", "nazwisko")
    @classmethod
    def waliduj_imie_nazwisko(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2: raise ValueError("Musi mieć co najmniej 2 znaki")
        if not REGEX_LITERY_PL.match(v): raise ValueError("Dozwolone są tylko litery, spacja i myślnik")
        return v

    @field_validator("pesel")
    @classmethod
    def waliduj_pesel_field(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^\d{11}$", v): raise ValueError("PESEL musi składać się z dokładnie 11 cyfr")
        if not waliduj_pesel(v): raise ValueError("Nieprawidłowy PESEL — błędna cyfra kontrolna")
        return v

    @field_validator("telefon")
    @classmethod
    def waliduj_telefon(cls, v: str) -> str:
        v = v.replace(" ", "")
        if not REGEX_TELEFON.match(v): raise ValueError("Telefon: 9 cyfr lub +48 i 9 cyfr")
        return v

    @field_validator("miejscowosc")
    @classmethod
    def waliduj_miejscowosc(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2: raise ValueError("Miejscowość musi mieć co najmniej 2 znaki")
        return v

    @field_validator("kod_pocztowy")
    @classmethod
    def waliduj_kod_pocztowy(cls, v: str) -> str:
        v = v.strip()
        if not REGEX_KOD_POCZTOWY.match(v): raise ValueError("Kod pocztowy musi być w formacie XX-XXX")
        return v

    @field_validator("nr_domu")
    @classmethod
    def waliduj_nr_domu(cls, v: str) -> str:
        v = v.strip()
        if not v: raise ValueError("Numer domu jest wymagany")
        if not REGEX_NR_DOMU.match(v): raise ValueError("Numer domu może zawierać tylko litery, cyfry, myślnik i ukośnik")
        return v

    @model_validator(mode="after")
    def waliduj_ulice(self):
        if not self.brak_ulicy:
            if not self.ulica or not self.ulica.strip(): raise ValueError("Podaj ulicę lub zaznacz 'brak ulicy'")
            self.ulica = self.ulica.strip()
        else: self.ulica = None
        return self

class DodajLekarzaRequest(BaseModel):
    email: str
    haslo: str
    imie: str
    nazwisko: str
    pesel: Optional[str] = None
    brak_peselu: bool = False
    telefon: Optional[str] = None
    npwz: str
    status_npwz: Literal["aktywny", "zawieszony", "wygasły"]
    waznosc_oc: date
    placowka_id: int = Field(gt=0)
    specjalizacje_ids: list[int] = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def waliduj_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not REGEX_EMAIL.match(v): raise ValueError("Nieprawidłowy format adresu email")
        return v

    @field_validator("haslo")
    @classmethod
    def waliduj_haslo(cls, v: str) -> str:
        if len(v) < 12: raise ValueError("Hasło musi mieć co najmniej 12 znaków")
        if not re.search(r"[A-Z]", v): raise ValueError("Hasło musi zawierać co najmniej jedną wielką literę")
        if not re.search(r"[a-z]", v): raise ValueError("Hasło musi zawierać co najmniej jedną małą literę")
        if not re.search(r"\d", v): raise ValueError("Hasło musi zawierać co najmniej jedną cyfrę")
        if not REGEX_ZNAK_SPECJALNY.search(v): raise ValueError("Hasło musi zawierać co najmniej jeden znak specjalny")
        return v

    @field_validator("imie", "nazwisko")
    @classmethod
    def waliduj_imie_nazwisko(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2: raise ValueError("Musi mieć co najmniej 2 znaki")
        if not REGEX_LITERY_PL.match(v): raise ValueError("Dozwolone są tylko litery, spacja i myślnik")
        return v

    @field_validator("npwz")
    @classmethod
    def waliduj_npwz(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^\d{7}$", v): raise ValueError("NPWZ musi składać się z dokładnie 7 cyfr")
        return v

    @field_validator("waznosc_oc")
    @classmethod
    def waliduj_waznosc_oc(cls, v: date) -> date:
        if v <= date.today(): raise ValueError("Data ważności OC musi być w przyszłości")
        return v

    @model_validator(mode="after")
    def waliduj_pesel_lub_brak(self):
        if self.brak_peselu:
            self.pesel = None
            return self
        if not self.pesel or not self.pesel.strip(): raise ValueError("PESEL jest wymagany (lub zaznacz 'brak PESEL')")
        pesel_clean = self.pesel.strip()
        if not re.match(r"^\d{11}$", pesel_clean): raise ValueError("PESEL musi składać się z dokładnie 11 cyfr")
        if not waliduj_pesel(pesel_clean): raise ValueError("Nieprawidłowy PESEL — błędna cyfra kontrolna")
        self.pesel = pesel_clean
        return self

class DodajPracownika(BaseModel):
    email: str
    haslo: str
    imie: str
    nazwisko: str
    pesel: Optional[str] = None
    brak_peselu: bool = False
    telefon: str
    rola: Literal["admin", "rejestracja"]

    @field_validator("email")
    @classmethod
    def waliduj_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not REGEX_EMAIL.match(v): raise ValueError("Nieprawidłowy format adresu email")
        return v

    @field_validator("haslo")
    @classmethod
    def waliduj_haslo(cls, v: str) -> str:
        if len(v) < 12: raise ValueError("Hasło musi mieć co najmniej 12 znaków")
        if not re.search(r"[A-Z]", v): raise ValueError("Hasło musi zawierać co najmniej jedną wielką literę")
        if not re.search(r"[a-z]", v): raise ValueError("Hasło musi zawierać co najmniej jedną małą literę")
        if not re.search(r"\d", v): raise ValueError("Hasło musi zawierać co najmniej jedną cyfrę")
        if not REGEX_ZNAK_SPECJALNY.search(v): raise ValueError("Hasło musi zawierać co najmniej jeden znak specjalny")
        return v

    @field_validator("imie", "nazwisko")
    @classmethod
    def waliduj_imie_nazwisko(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2: raise ValueError("Musi mieć co najmniej 2 znaki")
        if not REGEX_LITERY_PL.match(v): raise ValueError("Dozwolone są tylko litery, spacja i myślnik")
        return v

    @field_validator("telefon")
    @classmethod
    def waliduj_telefon(cls, v: str) -> str:
        v = v.replace(" ", "")
        if not REGEX_TELEFON.match(v): raise ValueError("Telefon: 9 cyfr lub +48 i 9 cyfr")
        return v

    @model_validator(mode="after")
    def waliduj_pesel_lub_brak(self):
        if self.brak_peselu:
            self.pesel = None
            return self
        if not self.pesel or not self.pesel.strip(): raise ValueError("PESEL jest wymagany (lub zaznacz 'brak PESEL')")
        pesel_clean = self.pesel.strip()
        if not re.match(r"^\d{11}$", pesel_clean): raise ValueError("PESEL musi składać się z dokładnie 11 cyfr")
        if not waliduj_pesel(pesel_clean): raise ValueError("Nieprawidłowy PESEL — błędna cyfra kontrolna")
        self.pesel = pesel_clean
        return self

class DodajGabinetRequest(BaseModel):
    numer: str
    status: Literal["Dostępny", "Niedostępny"] = "Dostępny"

    @field_validator("numer")
    @classmethod
    def waliduj_numer(cls, v: str) -> str:
        v = v.strip()
        if not v: raise ValueError("Numer gabinetu jest wymagany")
        if len(v) > 10: raise ValueError("Numer gabinetu max 10 znaków")
        return v

class ZmienStatusGabinetuRequest(BaseModel):
    status: Literal["Dostępny", "Niedostępny"]

class DodajGrafikRequest(BaseModel):
    lekarz_id: int = Field(gt=0)
    gabinet_id: int = Field(gt=0)
    data: date
    godzina_od: str
    godzina_do: str
    co_ile_minut: Literal[15, 20, 30, 45, 60] = 30

    @model_validator(mode="after")
    def waliduj_terminy(self):
        if self.data < date.today(): raise ValueError("Data musi być dzisiejsza lub z przyszłości")
        regex_godziny = r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$"
        if not re.match(regex_godziny, self.godzina_od): raise ValueError("godzina_od musi być poprawną godziną w formacie HH:MM (00:00 - 23:59)")
        if not re.match(regex_godziny, self.godzina_do): raise ValueError("godzina_do musi być poprawną godziną w formacie HH:MM (00:00 - 23:59)")
        if self.godzina_od >= self.godzina_do: raise ValueError("godzina_od musi być wcześniejsza niż godzina_do")
        return self

class RezerwacjaRequest(BaseModel):
    grafik_id: int = Field(gt=0)
    pacjent_id: Optional[int] = None

class AktualizacjaUzytkownikaRequest(BaseModel):
    rola: Optional[str] = None
    imie: Optional[str] = None
    nazwisko: Optional[str] = None
    telefon: Optional[str] = None
    miejscowosc: Optional[str] = None
    kod_pocztowy: Optional[str] = None
    ulica: Optional[str] = None
    nr_domu: Optional[str] = None
    nr_lokalu: Optional[str] = None
    specjalizacje_ids: Optional[list[int]] = None
    placowka_id: Optional[int] = None
    status_npwz: Optional[str] = None
    waznosc_oc: Optional[str] = None

class DokumentacjaRequest(BaseModel):
    kod_icd10: Optional[str] = None
    wywiad_lekarski: Optional[dict] = None