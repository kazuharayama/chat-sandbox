# ER図: chat-sandbox データベース

## 全体ER図

```mermaid
erDiagram
    %% === チャット系 ===
    chat_sessions {
        UUID id PK
        VARCHAR title
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    chat_messages {
        UUID id PK
        UUID session_id FK
        VARCHAR role "user | assistant"
        TEXT content
        JSONB sources "参照元ドキュメント"
        TIMESTAMPTZ created_at
    }

    chat_sessions ||--o{ chat_messages : "has"

    %% === ベクトルデータ (LangChain管理) ===
    langchain_pg_collection {
        UUID uuid PK
        VARCHAR name "chat_documents | image_documents"
        JSONB cmetadata
    }

    langchain_pg_embedding {
        UUID id PK
        UUID collection_id FK
        TEXT document
        JSONB cmetadata "source, document_id等"
        VECTOR embedding
    }

    langchain_pg_collection ||--o{ langchain_pg_embedding : "contains"

    %% === エージェント設定系 ===
    llm_models {
        UUID id PK
        VARCHAR name UK "gemma2:2b, llama3.2:3b等"
        VARCHAR provider "ollama | openai_compatible"
        VARCHAR deployment_name
        FLOAT temperature
        INT max_tokens
        BOOLEAN is_default
        JSONB config "プロバイダー固有設定"
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    agent_definitions {
        UUID id PK
        VARCHAR name UK "assistant等"
        VARCHAR display_name
        TEXT description
        VARCHAR agent_type "chat | search等"
        UUID llm_model_id FK
        BOOLEAN is_enabled
        INT sort_order
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    prompt_templates {
        UUID id PK
        UUID agent_id FK
        VARCHAR prompt_key "system_prompt | rag_section"
        TEXT content
        INT version
        BOOLEAN is_active
        VARCHAR updated_by
        TIMESTAMPTZ created_at
    }

    agent_parameters {
        UUID id PK
        UUID agent_id FK
        VARCHAR param_key UK "max_iterations等"
        TEXT param_value
        VARCHAR param_type "string | int | float"
        TEXT description
        TIMESTAMPTZ created_at
    }

    routing_rules {
        UUID id PK
        VARCHAR name UK
        TEXT description
        UUID source_agent_id FK
        TEXT condition_prompt
        JSONB routes "ルーティング先の定義"
        BOOLEAN is_enabled
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    knowledge_sources {
        UUID id PK
        VARCHAR name UK "chat_documents等"
        VARCHAR source_type "pgvector"
        VARCHAR collection_name
        JSONB config "similarity_k, threshold等"
        BOOLEAN is_enabled
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    %% === タスク管理系 ===
    tasks {
        UUID id PK
        VARCHAR title
        TEXT description
        VARCHAR status "todo | in_progress | done"
        INT sort_order
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    llm_models ||--o{ agent_definitions : "used by"
    agent_definitions ||--o{ prompt_templates : "has"
    agent_definitions ||--o{ agent_parameters : "has"
    agent_definitions ||--o{ routing_rules : "source"
```

## テーブルグループ

### チャット系
ユーザーとの会話を管理するテーブル群。

| テーブル | 説明 | レコード増加速度 |
|---------|------|----------------|
| `chat_sessions` | 会話セッション | 会話作成ごと |
| `chat_messages` | メッセージ履歴 (user/bot) | メッセージごと |

### タスク管理系
プロジェクトのタスクをカンバンボードで管理。

| テーブル | 説明 | レコード増加速度 |
|---------|------|----------------|
| `tasks` | タスク (TODO/進行中/完了) | タスク作成ごと |

### ベクトルデータ (LangChain管理)
LangChainのPGVectorが自動管理するテーブル。直接操作しない。

| テーブル | 説明 | レコード増加速度 |
|---------|------|----------------|
| `langchain_pg_collection` | コレクション定義 (chat_documents, image_documents) | 固定 |
| `langchain_pg_embedding` | ドキュメントの埋め込みベクトル | ドキュメントアップロードごと |

### エージェント設定系
管理画面から変更可能な設定テーブル群。

> **作成タイミング**: これらのテーブルは `docker/postgres/init.sql` ではなく、
> アプリ起動時に `backend/repositories/agent_config_repository.py::_ensure_tables` が
> `CREATE TABLE IF NOT EXISTS` で作成し、初期シードも投入する（スキーマの正本はリポジトリ側）。

| テーブル | 説明 | レコード増加速度 |
|---------|------|----------------|
| `llm_models` | LLMプロバイダー定義 (Ollama, OpenAI互換) | 手動登録 |
| `agent_definitions` | エージェント定義 | 手動登録 |
| `prompt_templates` | プロンプト (バージョン管理付き) | プロンプト更新ごと |
| `agent_parameters` | エージェントパラメータ | 手動設定 |
| `routing_rules` | エージェントルーティング条件 | 手動設定 |
| `knowledge_sources` | ベクトル検索設定 (similarity_k等) | 手動設定 |

## リレーション一覧

| 親テーブル | 子テーブル | 関係 | CASCADE |
|-----------|-----------|------|---------|
| `chat_sessions` | `chat_messages` | 1:N | ON DELETE CASCADE |
| `langchain_pg_collection` | `langchain_pg_embedding` | 1:N | - |
| `llm_models` | `agent_definitions` | 1:N | - |
| `agent_definitions` | `prompt_templates` | 1:N | ON DELETE CASCADE |
| `agent_definitions` | `agent_parameters` | 1:N | ON DELETE CASCADE |
| `agent_definitions` | `routing_rules` | 1:N | - |
