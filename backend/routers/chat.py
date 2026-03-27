from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from core.auth import require_group_member
from core.dependencies import get_chat_service
from models.chat import ChatRequest, ChatResponse
from services.chat_service import ChatService

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    user: dict = Depends(require_group_member),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        return chat_service.chat(request)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"チャット処理中にエラーが発生しました: {str(e)}",
        )


@router.post("/chat/stream")
async def chat_stream_endpoint(
    request: ChatRequest,
    user: dict = Depends(require_group_member),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        return StreamingResponse(
            chat_service.chat_stream(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"チャット処理中にエラーが発生しました: {str(e)}",
        )
