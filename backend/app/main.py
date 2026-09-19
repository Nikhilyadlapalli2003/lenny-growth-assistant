import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import artifacts, chat, health, sessions
from app.config import get_settings
from app.database import init_db

settings = get_settings()

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Grounded conversational assistant over Lenny's Podcast transcripts.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "detail": str(exc)},
    )


@app.on_event("startup")
async def on_startup():
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception:
        logger.exception("Database initialization failed - check DATABASE_URL / Postgres availability")


app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(artifacts.router)
