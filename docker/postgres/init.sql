-- Initialize database with extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE EXTENSION IF NOT EXISTS age;
LOAD 'age';
SET search_path = ag_catalog, "$user", public;

-- ============================================
-- Chat History
-- ============================================

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(200) NOT NULL DEFAULT '新しい会話',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'bot')),
    content TEXT NOT NULL,
    sources JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id, created_at);

-- ============================================
-- Agent Configuration
-- ============================================
-- NOTE: The agent-config tables (llm_models, agent_definitions,
-- prompt_templates, agent_parameters, routing_rules, knowledge_sources)
-- and their seed data are owned by the application, not this file.
-- They are created and seeded at startup by:
--   backend/repositories/agent_config_repository.py::_ensure_tables
-- Keeping a single source of truth avoids schema drift
-- (e.g. the legacy Azure-OpenAI columns / provider+config mismatch).
