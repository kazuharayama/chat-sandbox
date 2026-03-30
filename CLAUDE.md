# Chat Sandbox - プロジェクトガイド

汎用マルチエージェントRAG基盤。ドキュメント（テキスト・画像）をアップロードし、ベクトル検索を活用してLLMが質問に回答する。エージェント設定・プロンプトはDB管理で、管理画面から変更可能。

## アーキテクチャ概要

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐
│   Frontend  │────▶│   Backend   │────▶│     PostgreSQL      │
│  (React 19) │     │  (FastAPI)  │     │     (pgvector)      │
└─────────────┘     └─────────────┘     └─────────────────────┘
                          │
                    ┌─────┼──────────┐
                    ▼     ▼          ▼
             ┌──────────┐┌────────┐┌──────────┐
             │Azure     ││Ollama/ ││ Langfuse │
             │OpenAI    ││vLLM   ││(Tracing) │
             │(gpt-4o)  ││(local) ││          │
             └──────────┘└────────┘└──────────┘
```

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| Frontend | React 19, TypeScript, Vite 7, Tailwind CSS, lucide-react |
| Backend | Python 3.11, FastAPI, LangChain, Uvicorn |
| Database | PostgreSQL 16 + pgvector |
| LLM | Azure OpenAI gpt-4o / Ollama / vLLM (管理画面から切り替え可) |
| Embedding (テキスト) | Azure OpenAI text-embedding-ada-002 |
| Embedding (画像) | CLIP ViT-B-32 (sentence-transformers) |
| Vision | GPT-4o Vision (画像理解、base64送信) |
| ファイル保存 | Azure Blob Storage |
| 監視 | Langfuse v3（セルフホスト、docker-compose統合） |
| インフラ | Docker Compose (GPU/CPUプロファイル対応) |

## ディレクトリ構成

```
chat-sandbox/
├── backend/                    # FastAPI バックエンド
│   ├── main.py                # エントリポイント
│   ├── core/                  # 設定・DI・認証・ログ
│   │   ├── config.py         # Pydantic Settings (環境変数)
│   │   ├── dependencies.py   # FastAPI Depends (DIコンテナ)
│   │   ├── auth.py           # Entra ID認証 (グレースフルスキップ)
│   │   └── logging.py
│   ├── routers/               # APIルーター (薄い層)
│   │   ├── chat.py           # チャット (RAG + Vision)
│   │   ├── documents.py      # ドキュメント管理
│   │   ├── sessions.py       # セッション管理
│   │   ├── admin.py          # 管理API (モデル/プロンプト/ナレッジソース)
│   │   ├── context_lab.py    # Context Lab API (検索プレビュー/テスト実行)
│   │   └── speech.py         # 音声認識（スタブ）
│   ├── services/              # ビジネスロジック
│   │   ├── chat_service.py   # RAGチャット (DB動的読み込み)
│   │   ├── context_lab_service.py  # Context Lab (検索/コンテキスト/テスト)
│   │   ├── document_service.py     # ドキュメント処理
│   │   └── llm_factory.py    # LLMプロバイダーファクトリ (Azure/Ollama/vLLM)
│   ├── repositories/          # データアクセス
│   │   ├── vector_repository.py     # pgvector (テキスト)
│   │   ├── image_repository.py      # pgvector (CLIP画像)
│   │   ├── chat_repository.py       # チャット履歴
│   │   ├── document_repository.py   # Azure Blob Storage
│   │   └── agent_config_repository.py  # エージェント設定DB
│   ├── infrastructure/        # 外部サービス接続
│   │   └── clip_embeddings.py # CLIP ViT-B-32
│   └── models/                # Pydanticスキーマ
│       ├── chat.py
│       ├── document.py
│       └── agent_config.py
├── frontend/                   # React フロントエンド
│   └── src/
│       ├── App.tsx            # ルーティング (チャット/ドキュメント/Context Lab/管理)
│       ├── pages/
│       │   ├── Chat.tsx       # チャット画面 (Vision対応、サイドバー開閉式)
│       │   ├── Documents.tsx  # ドキュメント管理
│       │   ├── ContextLab.tsx # Context Lab (RAGパラメータ実験)
│       │   └── Admin.tsx      # 管理画面 (モデル/プロンプト/ナレッジソース)
│       ├── components/
│       │   ├── ChatWindow.tsx
│       │   ├── MessageInput.tsx
│       │   └── Sidebar.tsx
│       └── services/api.ts    # APIクライアント (全エンドポイント集約)
├── docker/                     # Docker設定
├── docs/                       # ドキュメント
│   ├── PRD.md                 # プロダクト要件定義書
│   ├── requirements/          # 要件定義書 (F0〜FE)
│   ├── architecture-flow.md   # アーキテクチャ・フロー図 (Mermaid)
│   ├── feature-catalog.md     # 機能カタログ
│   └── er-diagram.md          # ER図 (Mermaid)
├── scripts/
│   └── start.sh               # GPU自動検出 + 起動スクリプト
├── .env.example               # 環境変数テンプレート
└── docker-compose.yml          # ローカル開発用 (gpu/cpuプロファイル対応)
```

### レイヤー依存方向
```
routers → services → repositories → infrastructure
                ↑
            core/config（全層から参照可）
            models/（全層から参照可）
```

## 開発環境セットアップ

### 前提条件
- Docker & Docker Compose
- Azure OpenAI APIキー

### 環境変数 (.env)
```bash
cp .env.example .env
# Azure OpenAI キーを設定
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_ENDPOINT=<endpoint>
```

### 起動コマンド
```bash
# 全サービス起動（Azure OpenAIのみ）
docker compose up -d

# ローカルLLM付き起動（GPU自動検出）
./scripts/start.sh

# GPU/CPU明示指定
./scripts/start.sh --gpu   # Ollama(GPU) + vLLM
./scripts/start.sh --cpu   # Ollama(CPU)のみ

# Ollamaモデルダウンロード（初回のみ）
docker compose exec ollama-cpu ollama pull llama3.1:8b

# 停止
docker compose down

# DB再作成（スキーマ変更時）
docker compose down -v && docker compose up -d
```

### アクセスURL
- フロントエンド: http://localhost:5174
- バックエンドAPI: http://localhost:8000
- Nginx (本番模擬): http://localhost:8080
- Langfuse UI: http://localhost:3000
- Ollama: http://localhost:11434 (プロファイル起動時)
- PostgreSQL (アプリ): localhost:5435

### Langfuse初期アカウント
- Email: admin@local.dev
- Password: admin123
- API Public Key: pk-lf-local
- API Secret Key: sk-lf-local

## APIエンドポイント

### チャット
| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/chat` | RAG対応チャット (Vision対応) |
| POST | `/chat/stream` | SSEストリーミングチャット (Vision対応) |

### ドキュメント
| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/upload` | ドキュメントアップロード |
| GET | `/documents` | ドキュメント一覧 |
| DELETE | `/documents/{id}` | ドキュメント削除 |

### セッション
| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/sessions` | セッション作成 |
| GET | `/sessions` | セッション一覧 |
| GET | `/sessions/{id}/messages` | メッセージ取得 |
| DELETE | `/sessions/{id}` | セッション削除 |

### 管理
| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/admin/models` | LLMモデル一覧 |
| POST | `/admin/models` | モデル追加 |
| PUT | `/admin/models/{id}` | モデル更新 |
| GET | `/admin/agents` | エージェント一覧 |
| GET/PUT | `/admin/prompts/{agent_id}/{key}` | プロンプト取得/更新 |
| GET | `/admin/prompts/{agent_id}/{key}/versions` | バージョン履歴 |
| POST | `/admin/prompts/{agent_id}/{key}/rollback/{ver}` | ロールバック |
| GET | `/admin/knowledge-sources` | ナレッジソース一覧 |
| PUT | `/admin/knowledge-sources/{id}` | ナレッジソース更新 |
| POST | `/admin/cache/clear` | LLMキャッシュクリア |

### Context Lab
| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/admin/test-retrieval` | 検索プレビュー (チャンク+スコア) |
| POST | `/admin/context-preview` | コンテキストプレビュー (最終プロンプト全文) |
| POST | `/admin/test-chat` | テストチャット (SSEストリーミング) |

## LLMプロバイダー切り替え

管理画面の「LLMモデル」タブでプロバイダーを切り替え可能:

| プロバイダー | 実装クラス | 備考 |
|------------|-----------|------|
| `azure_openai` | AzureChatOpenAI | デフォルト。Vision対応 |
| `ollama` | ChatOllama | GPU/CPU両対応。docker compose profilesで起動 |
| `vllm` | ChatOpenAI (互換API) | GPU必須。高スループット |

`llm_factory.py` がproviderに応じたインスタンスを生成。TTL 60秒キャッシュ付き。

## コーディング規約

### Backend (Python)
- レイヤードアーキテクチャ: routers → services → repositories → infrastructure
- FastAPI Depends でDI
- LLMパラメータ・プロンプト・similarity_kはDB管理 (ハードコード禁止)
- `llm_factory.py` でプロバイダー切り替え

### Frontend (TypeScript/React)
- 関数コンポーネント + Hooks
- Tailwind CSSでスタイリング
- `services/api.ts` に全API呼び出しを集約
- lucide-react でアイコン

## データベース

### 接続情報 (開発環境)
```
Host: localhost:5435
Database: chat_db
User: chat_user
Password: chat_pass
```

### テーブル構成
- **チャット系**: `chat_sessions`, `chat_messages`
- **ベクトル系** (LangChain管理): `langchain_pg_collection`, `langchain_pg_embedding`
- **エージェント設定系**: `llm_models`, `agent_definitions`, `prompt_templates`, `agent_parameters`, `routing_rules`, `knowledge_sources`

詳細は `docs/er-diagram.md` を参照。

## よく使うコマンド

```bash
# バックエンドのみ再起動
docker compose restart backend

# DB再作成（スキーマ変更時）
docker compose down -v && docker compose up -d

# ログをリアルタイム監視
docker compose logs -f backend

# コンテナに入る
docker compose exec backend bash
docker compose exec postgres psql -U chat_user -d chat_db

# Ollamaモデル操作
docker compose exec ollama-cpu ollama list
docker compose exec ollama-cpu ollama pull <model>
```

## 関連ドキュメント

- [PRD](docs/PRD.md) — プロダクト要件定義書
- [要件定義書](docs/requirements/README.md) — F0〜FEのロードマップ
- [アーキテクチャ・フロー図](docs/architecture-flow.md) — Mermaidフロー図
- [機能カタログ](docs/feature-catalog.md) — 全機能の実装状況一覧
- [ER図](docs/er-diagram.md) — データベーススキーマ

## 注意事項

1. **CORS設定**: 現在は全オリジン許可 (`*`) — 本番では制限が必要
2. **認証**: `core/auth.py` 実装済みだが未統合 (FD)
3. **シークレット管理**: `.env` ファイルで管理。将来 Azure Key Vault に移行予定
4. **Langfuse**: 初期設定済み (pk-lf-local / sk-lf-local)、本番では変更が必要
5. **DBスキーマ変更時**: `docker compose down -v && docker compose up -d` が必要
