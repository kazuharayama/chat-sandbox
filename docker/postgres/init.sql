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

-- LLM Models
CREATE TABLE IF NOT EXISTS llm_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    deployment_name VARCHAR(200) NOT NULL,
    endpoint_env_var VARCHAR(100) DEFAULT 'AZURE_OPENAI_ENDPOINT',
    api_key_env_var VARCHAR(100) DEFAULT 'AZURE_OPENAI_API_KEY',
    api_version VARCHAR(50) DEFAULT '2024-08-01-preview',
    temperature FLOAT DEFAULT 0.7,
    max_tokens INT,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Agent Definitions
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
);

-- Prompt Templates (versioned)
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
);

CREATE INDEX IF NOT EXISTS idx_prompt_active
    ON prompt_templates(agent_id, prompt_key) WHERE is_active = true;

-- Agent Parameters
CREATE TABLE IF NOT EXISTS agent_parameters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agent_definitions(id) ON DELETE CASCADE,
    param_key VARCHAR(100) NOT NULL,
    param_value TEXT NOT NULL,
    param_type VARCHAR(20) DEFAULT 'string',
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(agent_id, param_key)
);

-- Routing Rules
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
);

-- Knowledge Sources
CREATE TABLE IF NOT EXISTS knowledge_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    collection_name VARCHAR(200) NOT NULL,
    config JSONB DEFAULT '{}',
    is_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================
-- Initial Data
-- ============================================

-- Default LLM model
INSERT INTO llm_models (name, deployment_name, temperature, is_default)
VALUES ('gpt-4o', 'gpt-4o', 0.7, true);

-- Default agent
INSERT INTO agent_definitions (name, display_name, description, agent_type, llm_model_id, is_enabled)
VALUES (
    'assistant',
    'AIアシスタント',
    'RAG対応の汎用チャットアシスタント',
    'chat',
    (SELECT id FROM llm_models WHERE name = 'gpt-4o'),
    true
);

-- Default system prompt
INSERT INTO prompt_templates (agent_id, prompt_key, content, version, is_active)
VALUES (
    (SELECT id FROM agent_definitions WHERE name = 'assistant'),
    'system_prompt',
    'あなたは親しみやすいAIアシスタントです。{language}で返答してください。
返答は会話的で親しみやすい口調にしてください。

{rag_section}',
    1,
    true
);

-- RAG section prompt
INSERT INTO prompt_templates (agent_id, prompt_key, content, version, is_active)
VALUES (
    (SELECT id FROM agent_definitions WHERE name = 'assistant'),
    'rag_section',
    '以下の関連ドキュメントの情報も参考にしてください。ドキュメントに関連情報がない場合は無視してください。

関連ドキュメント:
{context}

関連画像:
{image_context}',
    1,
    true
);

-- Knowledge sources
INSERT INTO knowledge_sources (name, source_type, collection_name, config)
VALUES
    ('chat_documents', 'pgvector', 'chat_documents', '{"similarity_k": 3}'),
    ('image_documents', 'pgvector', 'image_documents', '{"similarity_k": 2}');
