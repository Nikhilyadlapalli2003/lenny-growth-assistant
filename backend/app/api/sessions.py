import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import ChatSession, Message, get_db
from app.models.schemas import CreateSessionRequest, SessionDetailResponse, SessionResponse

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(req: CreateSessionRequest, db: AsyncSession = Depends(get_db)):
    session = ChatSession(
        title=req.title or "New chat",
        provider=req.provider or settings.DEFAULT_LLM_PROVIDER,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    msg_result = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at)
    )
    messages = msg_result.scalars().all()
    return SessionDetailResponse(
        id=session.id,
        title=session.title,
        provider=session.provider,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=messages,
    )


@router.get("", response_model=list[SessionResponse])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChatSession).order_by(ChatSession.updated_at.desc()))
    return result.scalars().all()
