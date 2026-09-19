"""
Pydantic request/response contracts for the public API.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------- Sessions ----------

class CreateSessionRequest(BaseModel):
    title: Optional[str] = Field(default=None, description="Optional human-readable session title")
    provider: Optional[Literal["ollama", "anthropic"]] = None


class SessionResponse(BaseModel):
    id: str
    title: str
    provider: str
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    sources: list[dict] = []
    provider_used: Optional[str] = None
    created_at: datetime


class SessionDetailResponse(SessionResponse):
    messages: list[MessageResponse] = []


# ---------- Chat ----------

class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1, max_length=8000)
    mode: Literal["default", "ship30", "artifact"] = "default"
    provider: Optional[Literal["ollama", "anthropic"]] = None


class SourceCitation(BaseModel):
    episode: str
    guest: Optional[str] = None
    timestamp: Optional[str] = None
    score: float


class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    content: str
    sources: list[SourceCitation] = []
    provider_used: str
    artifact_id: Optional[str] = None


# ---------- Artifacts ----------

class ArtifactResponse(BaseModel):
    id: str
    message_id: str
    artifact_type: Literal["markdown", "html"]
    title: str
    content: str
    created_at: datetime


# ---------- Health ----------

class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    database: bool
    ollama: bool
    vector_index: bool
    default_provider: str


# ---------- Errors ----------

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
