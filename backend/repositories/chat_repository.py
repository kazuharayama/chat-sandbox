import json
import logging
from typing import List, Optional

from sqlalchemy import create_engine, text

from models.chat import MessageInfo, SessionInfo

logger = logging.getLogger(__name__)


class ChatRepository:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self._ensure_tables()
        logger.info("ChatRepository initialized")

    def _ensure_tables(self) -> None:
        """Create tables if they don't exist."""
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    title VARCHAR(200) NOT NULL DEFAULT '新しい会話',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
                    role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    sources JSONB DEFAULT '[]',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_chat_messages_session
                ON chat_messages(session_id, created_at)
            """))
            conn.commit()

    def create_session(self, title: str = "新しい会話") -> SessionInfo:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("INSERT INTO chat_sessions (title) VALUES (:title) RETURNING id, title, created_at, updated_at"),
                {"title": title},
            )
            row = result.fetchone()
            conn.commit()
            return SessionInfo(id=str(row[0]), title=row[1], created_at=row[2], updated_at=row[3])

    def list_sessions(self) -> List[SessionInfo]:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, title, created_at, updated_at FROM chat_sessions ORDER BY updated_at DESC")
            )
            return [
                SessionInfo(id=str(r[0]), title=r[1], created_at=r[2], updated_at=r[3])
                for r in result.fetchall()
            ]

    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, title, created_at, updated_at FROM chat_sessions WHERE id = :id"),
                {"id": session_id},
            )
            row = result.fetchone()
            if not row:
                return None
            return SessionInfo(id=str(row[0]), title=row[1], created_at=row[2], updated_at=row[3])

    def update_session_title(self, session_id: str, title: str) -> None:
        with self.engine.connect() as conn:
            conn.execute(
                text("UPDATE chat_sessions SET title = :title, updated_at = now() WHERE id = :id"),
                {"title": title, "id": session_id},
            )
            conn.commit()

    def delete_session(self, session_id: str) -> None:
        with self.engine.connect() as conn:
            conn.execute(
                text("DELETE FROM chat_sessions WHERE id = :id"),
                {"id": session_id},
            )
            conn.commit()

    def add_message(self, session_id: str, role: str, content: str, sources: List[str] = None) -> MessageInfo:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO chat_messages (session_id, role, content, sources)
                    VALUES (:session_id, :role, :content, :sources)
                    RETURNING id, session_id, role, content, sources, created_at
                """),
                {
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                    "sources": json.dumps(sources or []),
                },
            )
            row = result.fetchone()
            # Touch session updated_at
            conn.execute(
                text("UPDATE chat_sessions SET updated_at = now() WHERE id = :id"),
                {"id": session_id},
            )
            conn.commit()
            return MessageInfo(
                id=str(row[0]),
                session_id=str(row[1]),
                role=row[2],
                content=row[3],
                sources=json.loads(row[4]) if row[4] else [],
                created_at=row[5],
            )

    def get_messages(self, session_id: str) -> List[MessageInfo]:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, session_id, role, content, sources, created_at
                    FROM chat_messages WHERE session_id = :session_id
                    ORDER BY created_at ASC
                """),
                {"session_id": session_id},
            )
            return [
                MessageInfo(
                    id=str(r[0]),
                    session_id=str(r[1]),
                    role=r[2],
                    content=r[3],
                    sources=json.loads(r[4]) if r[4] else [],
                    created_at=r[5],
                )
                for r in result.fetchall()
            ]
