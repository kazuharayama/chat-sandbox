import logging
from typing import List, Optional

from sqlalchemy import create_engine, text

from models.task import TaskInfo

logger = logging.getLogger(__name__)


class TaskRepository:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self._ensure_tables()
        logger.info("TaskRepository initialized")

    def _ensure_tables(self) -> None:
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    title VARCHAR(500) NOT NULL,
                    description TEXT,
                    status VARCHAR(20) NOT NULL DEFAULT 'todo'
                        CHECK (status IN ('todo', 'in_progress', 'done')),
                    sort_order INT DEFAULT 0,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status
                ON tasks(status, sort_order)
            """))
            conn.commit()

    def list_tasks(self, status: str = None) -> List[TaskInfo]:
        with self.engine.connect() as conn:
            if status:
                rows = conn.execute(
                    text("SELECT * FROM tasks WHERE status = :status ORDER BY sort_order, created_at"),
                    {"status": status},
                ).fetchall()
            else:
                rows = conn.execute(
                    text("SELECT * FROM tasks ORDER BY status, sort_order, created_at")
                ).fetchall()
            return [self._to_task(r) for r in rows]

    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        with self.engine.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM tasks WHERE id = :id"), {"id": task_id}
            ).fetchone()
            return self._to_task(row) if row else None

    def create_task(self, title: str, description: str = None, status: str = "todo") -> TaskInfo:
        with self.engine.connect() as conn:
            # Get max sort_order for the status
            max_order = conn.execute(
                text("SELECT COALESCE(MAX(sort_order), -1) FROM tasks WHERE status = :status"),
                {"status": status},
            ).scalar()
            row = conn.execute(
                text("""
                    INSERT INTO tasks (title, description, status, sort_order)
                    VALUES (:title, :description, :status, :sort_order)
                    RETURNING *
                """),
                {"title": title, "description": description, "status": status, "sort_order": max_order + 1},
            ).fetchone()
            conn.commit()
            return self._to_task(row)

    def update_task(self, task_id: str, title: str = None, description: str = None,
                    status: str = None, sort_order: int = None) -> Optional[TaskInfo]:
        with self.engine.connect() as conn:
            updates = []
            params = {"id": task_id}
            if title is not None:
                updates.append("title = :title")
                params["title"] = title
            if description is not None:
                updates.append("description = :description")
                params["description"] = description
            if status is not None:
                updates.append("status = :status")
                params["status"] = status
            if sort_order is not None:
                updates.append("sort_order = :sort_order")
                params["sort_order"] = sort_order
            if not updates:
                return self.get_task(task_id)
            updates.append("updated_at = now()")

            row = conn.execute(
                text(f"UPDATE tasks SET {', '.join(updates)} WHERE id = :id RETURNING *"),
                params,
            ).fetchone()
            conn.commit()
            return self._to_task(row) if row else None

    def delete_task(self, task_id: str) -> bool:
        with self.engine.connect() as conn:
            result = conn.execute(text("DELETE FROM tasks WHERE id = :id"), {"id": task_id})
            conn.commit()
            return result.rowcount > 0

    def _to_task(self, row) -> TaskInfo:
        return TaskInfo(
            id=str(row[0]), title=row[1], description=row[2],
            status=row[3], sort_order=row[4],
            created_at=row[5], updated_at=row[6],
        )
