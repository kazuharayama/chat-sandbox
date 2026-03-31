from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from core.auth import require_group_member
from core.dependencies import get_task_repository
from models.task import TaskCreateRequest, TaskUpdateRequest
from repositories.task_repository import TaskRepository

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(require_group_member)])


@router.get("")
async def list_tasks(
    status: Optional[str] = None,
    repo: TaskRepository = Depends(get_task_repository),
):
    return repo.list_tasks(status=status)


@router.post("")
async def create_task(
    body: TaskCreateRequest,
    repo: TaskRepository = Depends(get_task_repository),
):
    return repo.create_task(title=body.title, description=body.description, status=body.status)


@router.put("/{task_id}")
async def update_task(
    task_id: str,
    body: TaskUpdateRequest,
    repo: TaskRepository = Depends(get_task_repository),
):
    task = repo.update_task(
        task_id, title=body.title, description=body.description,
        status=body.status, sort_order=body.sort_order,
    )
    if not task:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    repo: TaskRepository = Depends(get_task_repository),
):
    if not repo.delete_task(task_id):
        raise HTTPException(status_code=404, detail="タスクが見つかりません")
    return {"status": "削除完了"}
