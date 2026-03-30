import json
import logging
from typing import List, Optional

from sqlalchemy import create_engine, text

from models.agent_config import (
    AgentInfo,
    AgentParameterInfo,
    KnowledgeSourceInfo,
    LLMModelInfo,
    LLMModelCreateRequest,
    PromptInfo,
    RoutingRuleInfo,
)

logger = logging.getLogger(__name__)


class AgentConfigRepository:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self._ensure_tables()
        logger.info("AgentConfigRepository initialized")

    def _ensure_tables(self) -> None:
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS llm_models (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    name VARCHAR(100) UNIQUE NOT NULL,
                    provider VARCHAR(50) NOT NULL DEFAULT 'azure_openai',
                    deployment_name VARCHAR(200) NOT NULL,
                    temperature FLOAT DEFAULT 0.7,
                    max_tokens INT,
                    is_default BOOLEAN DEFAULT false,
                    config JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT now(),
                    updated_at TIMESTAMPTZ DEFAULT now()
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS agent_definitions (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    name VARCHAR(100) UNIQUE NOT NULL,
                    display_name VARCHAR(200) NOT NULL,
                    description TEXT,
                    agent_type VARCHAR(50) NOT NULL,
                    llm_model_id UUID REFERENCES llm_models(id),
                    is_enabled BOOLEAN DEFAULT true,
                    sort_order INT DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    updated_at TIMESTAMPTZ DEFAULT now()
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS prompt_templates (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    agent_id UUID NOT NULL REFERENCES agent_definitions(id) ON DELETE CASCADE,
                    prompt_key VARCHAR(100) NOT NULL,
                    content TEXT NOT NULL,
                    version INT DEFAULT 1,
                    is_active BOOLEAN DEFAULT true,
                    updated_by VARCHAR(200),
                    created_at TIMESTAMPTZ DEFAULT now(),
                    UNIQUE(agent_id, prompt_key, version)
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS agent_parameters (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    agent_id UUID NOT NULL REFERENCES agent_definitions(id) ON DELETE CASCADE,
                    param_key VARCHAR(100) NOT NULL,
                    param_value TEXT NOT NULL,
                    param_type VARCHAR(20) DEFAULT 'string',
                    description TEXT,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    UNIQUE(agent_id, param_key)
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS routing_rules (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    name VARCHAR(100) UNIQUE NOT NULL,
                    description TEXT,
                    source_agent_id UUID NOT NULL REFERENCES agent_definitions(id),
                    condition_prompt TEXT NOT NULL,
                    routes JSONB NOT NULL,
                    is_enabled BOOLEAN DEFAULT true,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    updated_at TIMESTAMPTZ DEFAULT now()
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS knowledge_sources (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    name VARCHAR(100) UNIQUE NOT NULL,
                    source_type VARCHAR(50) NOT NULL,
                    collection_name VARCHAR(200) NOT NULL,
                    config JSONB DEFAULT '{}',
                    is_enabled BOOLEAN DEFAULT true,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    updated_at TIMESTAMPTZ DEFAULT now()
                )
            """))
            # Seed default data if empty
            count = conn.execute(text("SELECT COUNT(*) FROM llm_models")).scalar()
            if count == 0:
                conn.execute(text("""
                    INSERT INTO llm_models (name, provider, deployment_name, temperature, is_default, config)
                    VALUES ('gpt-4o', 'azure_openai', 'gpt-4o', 0.7, true,
                            '{"api_version": "2024-08-01-preview"}')
                """))
                conn.execute(text("""
                    INSERT INTO agent_definitions (name, display_name, description, agent_type, llm_model_id, is_enabled)
                    VALUES ('assistant', 'AIアシスタント', 'RAG対応の汎用チャットアシスタント', 'chat',
                            (SELECT id FROM llm_models WHERE name = 'gpt-4o'), true)
                """))
                conn.execute(text("""
                    INSERT INTO prompt_templates (agent_id, prompt_key, content, version, is_active)
                    VALUES (
                        (SELECT id FROM agent_definitions WHERE name = 'assistant'),
                        'system_prompt',
                        'あなたは親しみやすいAIアシスタントです。{language}で返答してください。
返答は会話的で親しみやすい口調にしてください。

{rag_section}',
                        1, true
                    )
                """))
                conn.execute(text("""
                    INSERT INTO prompt_templates (agent_id, prompt_key, content, version, is_active)
                    VALUES (
                        (SELECT id FROM agent_definitions WHERE name = 'assistant'),
                        'rag_section',
                        '以下の関連ドキュメントの情報も参考にしてください。ドキュメントに関連情報がない場合は無視してください。

関連ドキュメント:
{context}

関連画像:
{image_context}',
                        1, true
                    )
                """))
                conn.execute(text("""
                    INSERT INTO knowledge_sources (name, source_type, collection_name, config) VALUES
                    ('chat_documents', 'pgvector', 'chat_documents', '{"similarity_k": 3}'),
                    ('image_documents', 'pgvector', 'image_documents', '{"similarity_k": 2}')
                """))
            conn.commit()

    # --- LLM Models ---

    def list_models(self) -> List[LLMModelInfo]:
        with self.engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM llm_models ORDER BY name")).fetchall()
            return [self._to_model(r) for r in rows]

    def get_model(self, model_id: str) -> Optional[LLMModelInfo]:
        with self.engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM llm_models WHERE id = :id"), {"id": model_id}).fetchone()
            return self._to_model(row) if row else None

    def get_default_model(self) -> Optional[LLMModelInfo]:
        with self.engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM llm_models WHERE is_default = true LIMIT 1")).fetchone()
            return self._to_model(row) if row else None

    def _to_model(self, row) -> LLMModelInfo:
        config = row[7] if row[7] else {}
        if isinstance(config, str):
            config = json.loads(config)
        return LLMModelInfo(
            id=str(row[0]), name=row[1], provider=row[2], deployment_name=row[3],
            temperature=row[4], max_tokens=row[5], is_default=row[6], config=config,
        )

    def create_model(self, req: LLMModelCreateRequest) -> LLMModelInfo:
        with self.engine.connect() as conn:
            row = conn.execute(
                text("""
                    INSERT INTO llm_models (name, provider, deployment_name, temperature, max_tokens, is_default, config)
                    VALUES (:name, :provider, :deployment_name, :temperature, :max_tokens, :is_default, :config::jsonb)
                    RETURNING *
                """),
                {
                    "name": req.name, "provider": req.provider, "deployment_name": req.deployment_name,
                    "temperature": req.temperature, "max_tokens": req.max_tokens,
                    "is_default": req.is_default, "config": json.dumps(req.config or {}),
                },
            ).fetchone()
            conn.commit()
            return self._to_model(row)

    def update_model(self, model_id: str, temperature: float = None, max_tokens: int = None,
                     is_default: bool = None, config: dict = None) -> Optional[LLMModelInfo]:
        with self.engine.connect() as conn:
            # If setting as default, clear other defaults first
            if is_default:
                conn.execute(text("UPDATE llm_models SET is_default = false"))

            updates = []
            params = {"id": model_id}
            if temperature is not None:
                updates.append("temperature = :temperature")
                params["temperature"] = temperature
            if max_tokens is not None:
                updates.append("max_tokens = :max_tokens")
                params["max_tokens"] = max_tokens
            if is_default is not None:
                updates.append("is_default = :is_default")
                params["is_default"] = is_default
            if config is not None:
                updates.append("config = :config::jsonb")
                params["config"] = json.dumps(config)
            updates.append("updated_at = now()")

            row = conn.execute(
                text(f"UPDATE llm_models SET {', '.join(updates)} WHERE id = :id RETURNING *"),
                params,
            ).fetchone()
            conn.commit()
            return self._to_model(row) if row else None

    def update_knowledge_source(self, source_id: str, config: dict = None,
                                is_enabled: bool = None) -> Optional[KnowledgeSourceInfo]:
        with self.engine.connect() as conn:
            updates = []
            params = {"id": source_id}
            if config is not None:
                updates.append("config = :config::jsonb")
                params["config"] = json.dumps(config)
            if is_enabled is not None:
                updates.append("is_enabled = :is_enabled")
                params["is_enabled"] = is_enabled
            updates.append("updated_at = now()")

            row = conn.execute(
                text(f"UPDATE knowledge_sources SET {', '.join(updates)} WHERE id = :id RETURNING *"),
                params,
            ).fetchone()
            conn.commit()
            if not row:
                return None
            return KnowledgeSourceInfo(
                id=str(row[0]), name=row[1], source_type=row[2],
                collection_name=row[3], config=json.loads(row[4]) if isinstance(row[4], str) else row[4],
                is_enabled=row[5],
            )

    # --- Agent Definitions ---

    def list_agents(self) -> List[AgentInfo]:
        with self.engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM agent_definitions ORDER BY sort_order, name")).fetchall()
            return [self._to_agent(r) for r in rows]

    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        with self.engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM agent_definitions WHERE id = :id"), {"id": agent_id}).fetchone()
            return self._to_agent(row) if row else None

    def get_agent_by_name(self, name: str) -> Optional[AgentInfo]:
        with self.engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM agent_definitions WHERE name = :name"), {"name": name}).fetchone()
            return self._to_agent(row) if row else None

    def _to_agent(self, row) -> AgentInfo:
        return AgentInfo(
            id=str(row[0]), name=row[1], display_name=row[2], description=row[3],
            agent_type=row[4], llm_model_id=str(row[5]) if row[5] else None,
            is_enabled=row[6], sort_order=row[7],
        )

    # --- Prompt Templates ---

    def get_active_prompts(self, agent_id: str) -> List[PromptInfo]:
        with self.engine.connect() as conn:
            rows = conn.execute(
                text("SELECT * FROM prompt_templates WHERE agent_id = :agent_id AND is_active = true ORDER BY prompt_key"),
                {"agent_id": agent_id},
            ).fetchall()
            return [self._to_prompt(r) for r in rows]

    def get_active_prompt(self, agent_id: str, prompt_key: str) -> Optional[PromptInfo]:
        with self.engine.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM prompt_templates WHERE agent_id = :agent_id AND prompt_key = :key AND is_active = true ORDER BY version DESC LIMIT 1"),
                {"agent_id": agent_id, "key": prompt_key},
            ).fetchone()
            return self._to_prompt(row) if row else None

    def get_prompt_versions(self, agent_id: str, prompt_key: str) -> List[PromptInfo]:
        with self.engine.connect() as conn:
            rows = conn.execute(
                text("SELECT * FROM prompt_templates WHERE agent_id = :agent_id AND prompt_key = :key ORDER BY version DESC"),
                {"agent_id": agent_id, "key": prompt_key},
            ).fetchall()
            return [self._to_prompt(r) for r in rows]

    def update_prompt(self, agent_id: str, prompt_key: str, content: str, updated_by: str = None) -> PromptInfo:
        """Create new version and deactivate old ones."""
        with self.engine.connect() as conn:
            # Get current max version
            result = conn.execute(
                text("SELECT COALESCE(MAX(version), 0) FROM prompt_templates WHERE agent_id = :agent_id AND prompt_key = :key"),
                {"agent_id": agent_id, "key": prompt_key},
            )
            max_version = result.scalar()

            # Deactivate old versions
            conn.execute(
                text("UPDATE prompt_templates SET is_active = false WHERE agent_id = :agent_id AND prompt_key = :key"),
                {"agent_id": agent_id, "key": prompt_key},
            )

            # Insert new version
            row = conn.execute(
                text("""
                    INSERT INTO prompt_templates (agent_id, prompt_key, content, version, is_active, updated_by)
                    VALUES (:agent_id, :key, :content, :version, true, :updated_by)
                    RETURNING *
                """),
                {"agent_id": agent_id, "key": prompt_key, "content": content, "version": max_version + 1, "updated_by": updated_by},
            ).fetchone()
            conn.commit()
            return self._to_prompt(row)

    def rollback_prompt(self, agent_id: str, prompt_key: str, version: int) -> Optional[PromptInfo]:
        """Reactivate a specific version."""
        with self.engine.connect() as conn:
            conn.execute(
                text("UPDATE prompt_templates SET is_active = false WHERE agent_id = :agent_id AND prompt_key = :key"),
                {"agent_id": agent_id, "key": prompt_key},
            )
            conn.execute(
                text("UPDATE prompt_templates SET is_active = true WHERE agent_id = :agent_id AND prompt_key = :key AND version = :version"),
                {"agent_id": agent_id, "key": prompt_key, "version": version},
            )
            conn.commit()
            return self.get_active_prompt(agent_id, prompt_key)

    def _to_prompt(self, row) -> PromptInfo:
        return PromptInfo(
            id=str(row[0]), agent_id=str(row[1]), prompt_key=row[2],
            content=row[3], version=row[4], is_active=row[5],
            updated_by=row[6], created_at=row[7],
        )

    # --- Agent Parameters ---

    def get_parameters(self, agent_id: str) -> List[AgentParameterInfo]:
        with self.engine.connect() as conn:
            rows = conn.execute(
                text("SELECT * FROM agent_parameters WHERE agent_id = :agent_id ORDER BY param_key"),
                {"agent_id": agent_id},
            ).fetchall()
            return [AgentParameterInfo(
                id=str(r[0]), agent_id=str(r[1]), param_key=r[2],
                param_value=r[3], param_type=r[4], description=r[5],
            ) for r in rows]

    # --- Knowledge Sources ---

    def list_knowledge_sources(self) -> List[KnowledgeSourceInfo]:
        with self.engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM knowledge_sources WHERE is_enabled = true ORDER BY name")).fetchall()
            return [KnowledgeSourceInfo(
                id=str(r[0]), name=r[1], source_type=r[2],
                collection_name=r[3], config=json.loads(r[4]) if isinstance(r[4], str) else r[4],
                is_enabled=r[5],
            ) for r in rows]

    # --- Routing Rules ---

    def list_routing_rules(self, source_agent_id: str = None) -> List[RoutingRuleInfo]:
        with self.engine.connect() as conn:
            if source_agent_id:
                rows = conn.execute(
                    text("SELECT * FROM routing_rules WHERE source_agent_id = :id AND is_enabled = true"),
                    {"id": source_agent_id},
                ).fetchall()
            else:
                rows = conn.execute(text("SELECT * FROM routing_rules WHERE is_enabled = true")).fetchall()
            return [RoutingRuleInfo(
                id=str(r[0]), name=r[1], description=r[2], source_agent_id=str(r[3]),
                condition_prompt=r[4], routes=json.loads(r[5]) if isinstance(r[5], str) else r[5],
                is_enabled=r[6],
            ) for r in rows]
