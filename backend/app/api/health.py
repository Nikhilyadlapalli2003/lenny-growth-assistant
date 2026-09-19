import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.schemas import HealthResponse
from app.providers.ollama_provider import OllamaProvider

router = APIRouter(prefix="/api", tags=["Health"])
logger = logging.getLogger(__name__)
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health(db: AsyncSession = Depends(get_db)):
    db_ok = False
    vector_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
        result = await db.execute(text("SELECT to_regclass('transcript_chunks')"))
        vector_ok = result.scalar() is not None
    except Exception:
        logger.exception("Health check DB failure")

    ollama_ok = await OllamaProvider().health_check()

    status = "ok" if db_ok and (ollama_ok or settings.DEFAULT_LLM_PROVIDER == "anthropic") else "degraded"
    return HealthResponse(
        status=status,
        database=db_ok,
        ollama=ollama_ok,
        vector_index=vector_ok,
        default_provider=settings.DEFAULT_LLM_PROVIDER,
    )
