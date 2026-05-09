from database import engine
from models import Base

print(" Łączenie z Dockerem... Rozpoczynam budowę struktury MediSync!")

Base.metadata.create_all(bind=engine)

print("Sukces! Wszystkie tabele z diagramu ERD zostały utworzone w bazie danych.")