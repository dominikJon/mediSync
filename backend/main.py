import os
import secrets
import base64
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

# Importujemy nasze wyodrębnione routery
from routers import auth, admin, raporty, gabinety, grafiki, wizyty, lekarz, pacjent

# Konfiguracja środowiskowa z .env
ENV = os.getenv("ENV", "development")
SWAGGER_USERNAME = os.getenv("SWAGGER_USERNAME")
SWAGGER_PASSWORD = os.getenv("SWAGGER_PASSWORD")

app = FastAPI(
    title="MediSync API",
    docs_url="/docs" if ENV == "development" else None,
    redoc_url=None,
    openapi_url="/openapi.json" if ENV == "development" else None,
)

# MIDDLEWARE CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OCHRONA SWAGGERA
@app.middleware("http")
async def swagger_basic_auth(request: Request, call_next):
    if request.url.path in ["/docs", "/openapi.json"]:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return Response(
                status_code=401,
                headers={"WWW-Authenticate": "Basic realm='MediSync API'"},
                content="Unauthorized",
            )
        try:
            decoded = base64.b64decode(auth_header.split(" ")[1]).decode()
            username, password = decoded.split(":", 1)
            if not (secrets.compare_digest(username, SWAGGER_USERNAME) and
                    secrets.compare_digest(password, SWAGGER_PASSWORD)):
                raise ValueError
        except Exception:
            return Response(
                status_code=401,
                headers={"WWW-Authenticate": "Basic realm='MediSync API'"},
                content="Unauthorized",
            )
    return await call_next(request)


# podpiecie routerow
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(raporty.router)
app.include_router(gabinety.router)
app.include_router(grafiki.router)
app.include_router(wizyty.router)
app.include_router(lekarz.router)
app.include_router(pacjent.router)