"""
Ingestion pipeline: reads transcript files from data/raw/, extracts episode
metadata from filenames/front-matter, chunks the text, embeds each chunk,
and upserts into the transcript_chunks table (pgvector).

Expected filename convention (customize as needed):
    <episode-title>__<guest-name>.md

Re-running this script is destructive-safe: it deletes existing chunks for
an episode title before re-inserting, so it can be used to refresh content.

Usage:
    python scripts/ingest.py
"""
import asyncio
import logging
import sys
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.append(str(Path(__file__).resolve().parent.parent))
from sqlalchemy import delete, text as sa_text  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.database import AsyncSessionLocal, TranscriptChunk, engine  # noqa: E402
from app.rag.chunking import chunk_transcript  # noqa: E402
from app.rag.embeddings import embed_batch  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
settings = get_settings()


def parse_filename(path: Path) -> tuple[str, str]:
    stem = path.stem
    if "__" in stem:
        title, guest = stem.split("__", 1)
    else:
        title, guest = stem, "Unknown"
    return title.replace("-", " ").strip(), guest.replace("-", " ").strip()


async def ensure_extension():
    async with engine.begin() as conn:
        await conn.execute(sa_text("CREATE EXTENSION IF NOT EXISTS vector"))


async def ingest_file(path: Path):
    episode_title, guest_name = parse_filename(path)
    raw_text = path.read_text(encoding="utf-8", errors="ignore")
    chunks = chunk_transcript(
        raw_text,
        target_tokens=settings.CHUNK_TARGET_TOKENS,
        overlap_tokens=settings.CHUNK_OVERLAP_TOKENS,
    )
    if not chunks:
        logger.warning("No chunks produced for %s - skipping", path.name)
        return 0

    embeddings = await embed_batch(chunks)

    async with AsyncSessionLocal() as session:
        await session.execute(delete(TranscriptChunk).where(TranscriptChunk.episode_title == episode_title))
        for i, (chunk_text, vector) in enumerate(zip(chunks, embeddings)):
            session.add(
                TranscriptChunk(
                    episode_title=episode_title,
                    guest_name=guest_name,
                    episode_url=None,
                    timestamp_ref=f"chunk {i + 1}/{len(chunks)}",
                    chunk_index=i,
                    chunk_text=chunk_text,
                    embedding=vector,
                )
            )
        await session.commit()

    logger.info("Ingested %d chunks from %s (%s)", len(chunks), path.name, episode_title)
    return len(chunks)


async def main():
    if not RAW_DIR.exists() or not any(RAW_DIR.iterdir()):
        raise SystemExit(
            f"No transcripts found in {RAW_DIR}. Run scripts/download_transcripts.py first, "
            "or drop .txt/.md episode files in that folder."
        )

    await ensure_extension()

    total = 0
    files = sorted(list(RAW_DIR.glob("*.txt")) + list(RAW_DIR.glob("*.md")))
    for f in files:
        total += await ingest_file(f)

    logger.info("Ingestion complete: %d files, %d chunks total", len(files), total)


if __name__ == "__main__":
    asyncio.run(main())

