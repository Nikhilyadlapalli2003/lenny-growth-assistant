"""
Embedding function wrapper. Uses sentence-transformers locally so ingestion
and query-time embedding never depend on a network call or paid API.
"""
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


@lru_cache
def _get_model():
    from sentence_transformers import SentenceTransformer
    from app.config import get_settings

    settings = get_settings()
    logger.info("Loading embedding model %s", settings.EMBEDDING_MODEL)
    return SentenceTransformer(settings.EMBEDDING_MODEL)


async def embed_text(text: str) -> list[float]:
    model = _get_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


async def embed_batch(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
    return [v.tolist() for v in vectors]
