from fastapi import APIRouter, Depends, HTTPException

from core.dependencies import get_chat_service
from models.chat import ChatRequest, ChatResponse
from services.chat_service import ChatService

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        return chat_service.chat(request)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"チャット処理中にエラーが発生しました: {str(e)}",
        )
