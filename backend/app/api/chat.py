"""
Core chat endpoint: retrieves grounded context, routes to the selected skill
(default QA / ship30 essay), streams tokens from the selected provider, and
persists the resulting message + any generated artifact.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Artifact, ChatSession, Message, get_db
from app.models.schemas import ChatRequest, ChatResponse, SourceCitation
from app.providers.factory import get_provider
from app.rag.retriever import TranscriptRetriever
from app.skills.artifact_generator import ARTIFACT_SYSTEM_SUFFIX, extract_artifact
from app.skills.grounded_qa import build_grounded_prompt
from app.skills.ship30_writer import build_ship30_prompt

router = APIRouter(prefix="/api/chat", tags=["Chat"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
    x_llm_provider: str | None = Header(default=None),
):
    session_result = await db.execute(select(ChatSession).where(ChatSession.id == req.session_id))
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {req.session_id} not found")

    # 1. Persist the user turn
    user_msg = Message(session_id=session.id, role="user", content=req.message)
    db.add(user_msg)
    await db.flush()

    # 2. Retrieve grounded context
    retriever = TranscriptRetriever(db)
    try:
        chunks = await retriever.retrieve(req.message)
    except Exception:
        logger.exception("Retrieval failed; continuing with empty context")
        chunks = []

    # 3. Build the system prompt for the requested skill
    if req.mode == "ship30":
        system_prompt = build_ship30_prompt(chunks)
    else:
        system_prompt = build_grounded_prompt(chunks) + ARTIFACT_SYSTEM_SUFFIX

    # 4. Resolve provider (request body > header > session default > global default)
    provider_name = req.provider or x_llm_provider or session.provider
    provider = get_provider(provider_name)

    # 5. Build conversation history for context
    history_result = await db.execute(
        select(Message).where(Message.session_id == session.id).order_by(Message.created_at)
    )
    history = [{"role": m.role, "content": m.content} for m in history_result.scalars().all() if m.role in ("user", "assistant")]

    full_text = ""
    async for token in provider.generate(messages=history, system_prompt=system_prompt):
        full_text += token

    reply_text, artifact_data = extract_artifact(full_text)

    sources = [
        SourceCitation(episode=c["episode"], guest=c.get("guest"), timestamp=c.get("timestamp"), score=c["score"])
        for c in chunks
    ]

    assistant_msg = Message(
        session_id=session.id,
        role="assistant",
        content=reply_text,
        sources=[s.model_dump() for s in sources],
        provider_used=provider.name,
    )
    db.add(assistant_msg)
    await db.flush()

    artifact_id = None
    if artifact_data:
        artifact = Artifact(message_id=assistant_msg.id, **artifact_data)
        db.add(artifact)
        await db.flush()
        artifact_id = artifact.id

    await db.commit()

    return ChatResponse(
        session_id=session.id,
        message_id=assistant_msg.id,
        content=reply_text,
        sources=sources,
        provider_used=provider.name,
        artifact_id=artifact_id,
    )
