import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from models import Base

load_dotenv()
DB_PASSWORD = os.getenv("DB_PASSWORD")

LOCAL_DB_URL = f"postgresql://admin:{DB_PASSWORD}@localhost:5432/medisync"
engine_local = create_engine(LOCAL_DB_URL)

print("Łączenie z bazą (localhost)... Rozpoczynam całkowite czyszczenie bazy MediSync!")

# Usuwanie przy użyciu lokalnego silnika
Base.metadata.drop_all(bind=engine_local)

print("Sukces! Baza została zresetowana do zera.")