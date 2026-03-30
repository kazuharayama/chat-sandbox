from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    language: str = "日本語"
    hasAttachment: bool = False
    use_rag: bool = True
    image_base64: Optional[str] = None  # base64 encoded image for Vision
    image_mime_type: Optional[str] = None  # e.g. "image/png"


class ChatResponse(BaseModel):
    response: str
    sources: list[str] = []
    session_id: Optional[str] = None


class SessionInfo(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class MessageInfo(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    sources: list[str] = []
    created_at: datetime
