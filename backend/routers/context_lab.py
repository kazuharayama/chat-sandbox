from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from core.dependencies import get_context_lab_service
from services.context_lab_service import ContextLabService

router = APIRouter(prefix="/admin", tags=["context-lab"])


class TestRetrievalRequest(BaseModel):
    query: str
    similarity_k: int = 3
    threshold: float = 0.0
    collection_name: str = "chat_documents"


class ContextPreviewRequest(BaseModel):
    query: str
    similarity_k: int = 3
    threshold: float = 0.0
    language: str = "日本語"
    system_prompt_override: Optional[str] = None


class TestChatRequest(BaseModel):
    query: str
    similarity_k: int = 3
    threshold: float = 0.0
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    language: str = "日本語"
    system_prompt_override: Optional[str] = None


@router.post("/test-retrieval")
async def test_retrieval(
    body: TestRetrievalRequest,
    svc: ContextLabService = Depends(get_context_lab_service),
):
    return svc.test_retrieval(
        query=body.query,
        similarity_k=body.similarity_k,
        threshold=body.threshold,
        collection_name=body.collection_name,
    )


@router.post("/context-preview")
async def context_preview(
    body: ContextPreviewRequest,
    svc: ContextLabService = Depends(get_context_lab_service),
):
    return svc.build_context_preview(
        query=body.query,
        similarity_k=body.similarity_k,
        threshold=body.threshold,
        language=body.language,
        system_prompt_override=body.system_prompt_override,
    )


@router.post("/test-chat")
async def test_chat(
    body: TestChatRequest,
    svc: ContextLabService = Depends(get_context_lab_service),
):
    return StreamingResponse(
        svc.test_chat_stream(
            query=body.query,
            similarity_k=body.similarity_k,
            threshold=body.threshold,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            language=body.language,
            system_prompt_override=body.system_prompt_override,
        ),
        media_type="text/event-stream",
    )
