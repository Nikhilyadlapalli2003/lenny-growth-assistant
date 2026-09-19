"""
pgvector-backed similarity retrieval over ingested transcript chunks.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.rag.embeddings import embed_text

settings = get_settings()


class TranscriptRetriever:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> list[dict]:
        top_k = top_k or settings.RETRIEVAL_TOP_K
        similarity_threshold = (
            similarity_threshold if similarity_threshold is not None else settings.RETRIEVAL_SIMILARITY_THRESHOLD
        )
        query_vector = await embed_text(query)

        stmt = text(
            """
            SELECT
                episode_title,
                guest_name,
                episode_url,
                timestamp_ref,
                chunk_text,
                1 - (embedding <=> CAST(:vector AS vector)) AS similarity_score
            FROM transcript_chunks
            WHERE 1 - (embedding <=> CAST(:vector AS vector)) >= :threshold
            ORDER BY similarity_score DESC
            LIMIT :limit
            """
        )
        result = await self.session.execute(
            stmt,
            {"vector": str(query_vector), "threshold": similarity_threshold, "limit": top_k},
        )
        rows = result.mappings().all()
        return [
            {
                "episode": r["episode_title"],
                "guest": r["guest_name"],
                "url": r["episode_url"],
                "timestamp": r["timestamp_ref"],
                "text": r["chunk_text"],
                "score": float(r["similarity_score"]),
            }
            for r in rows
        ]
