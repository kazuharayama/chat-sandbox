from fastapi import APIRouter, Depends, HTTPException

from core.auth import require_group_member
from core.dependencies import get_chat_repository
from repositories.chat_repository import ChatRepository

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("")
async def create_session(
    user: dict = Depends(require_group_member),
    chat_repo: ChatRepository = Depends(get_chat_repository),
):
    session = chat_repo.create_session()
    return session


@router.get("")
async def list_sessions(
    user: dict = Depends(require_group_member),
    chat_repo: ChatRepository = Depends(get_chat_repository),
):
    return chat_repo.list_sessions()


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    user: dict = Depends(require_group_member),
    chat_repo: ChatRepository = Depends(get_chat_repository),
):
    session = chat_repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    return session


@router.get("/{session_id}/messages")
async def get_messages(
    session_id: str,
    user: dict = Depends(require_group_member),
    chat_repo: ChatRepository = Depends(get_chat_repository),
):
    return chat_repo.get_messages(session_id)


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    user: dict = Depends(require_group_member),
    chat_repo: ChatRepository = Depends(get_chat_repository),
):
    chat_repo.delete_session(session_id)
    return {"status": "削除完了"}
