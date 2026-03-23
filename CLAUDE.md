# Chat Sandbox - プロジェクトガイド

RAG (Retrieval Augmented Generation) 機能を持つフルスタックAIチャットアプリケーション

## アーキテクチャ概要

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐
│   Frontend  │────▶│   Backend   │────▶│     PostgreSQL      │
│  (React 19) │     │  (FastAPI)  │     │     (pgvector)      │
└─────────────┘     └─────────────┘     └─────────────────────┘
                          │
                    ┌─────┴──────┐
                    ▼            ▼
             ┌───────────┐ ┌──────────┐
             │Azure OpenAI│ │ Langfuse │
             │  (gpt-4o) │ │(Tracing) │
             └───────────┘ └──────────┘
```

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| Frontend | React 19, TypeScript, Vite 7, Tailwind CSS |
| Backend | Python 3.11, FastAPI, LangChain, Uvicorn |
| Database | PostgreSQL 16 + pgvector |
| LLM | Azure OpenAI gpt-4o (AzureChatOpenAI) |
| Embedding | Azure OpenAI text-embedding-ada-002 (AzureOpenAIEmbeddings) |
| 監視 | Langfuse v3（セルフホスト、docker-compose統合） |
| インフラ | Docker Compose |

## ディレクトリ構成

```
chat-sandbox/
├── backend/                    # FastAPI バックエンド
│   ├── app.py                 # アプリケーションエントリポイント
│   ├── config.py              # 設定管理（Azure OpenAI設定）
│   ├── routers/               # APIルーター
│   │   ├── chat.py           # チャットエンドポイント (RAG対応)
│   │   ├── documents.py      # ドキュメント管理
│   │   └── speech.py         # 音声認識（スタブ）
│   ├── utils/                 # ユーティリティ
│   │   ├── pgvector_manager.py   # ベクトルストア管理
│   │   └── db_connection.py      # DB接続プール
│   └── docs/                  # アップロードされたドキュメント保存先
├── frontend/                   # React フロントエンド
│   └── src/
│       ├── pages/             # ページコンポーネント
│       │   ├── Chat.tsx      # チャット画面
│       │   └── Documents.tsx # ドキュメント管理画面
│       ├── components/        # UIコンポーネント
│       └── services/api.ts    # APIクライアント
├── docker/                     # Docker設定
│   ├── backend/               # バックエンドDockerfile
│   ├── frontend/              # フロントエンドDockerfile
│   ├── postgres/              # PostgreSQL (pgvector)
│   └── nginx/                 # リバースプロキシ
├── docs/                       # プロジェクトドキュメント
│   └── PRD.md                 # プロダクト要件定義書
├── .env.example               # 環境変数テンプレート
└── docker-compose.yml          # ローカル開発用（Langfuse含む）
```

## 開発環境セットアップ

### 前提条件
- Docker & Docker Compose
- Azure OpenAI APIキー（cmos-maintenance-appのterraform outputから取得）

### 環境変数 (.env)
```bash
# .env.example をコピーして .env を作成
cp .env.example .env

# Azure OpenAI キーを設定
AZURE_OPENAI_API_KEY=<terraform output -raw openai_primary_key>
AZURE_OPENAI_ENDPOINT=<terraform output -raw openai_endpoint>
```

### 起動コマンド
```bash
# 全サービス起動（アプリ + Langfuse）
docker compose up -d

# ログ確認
docker compose logs -f backend
docker compose logs -f frontend

# 停止
docker compose down
```

### アクセスURL
- フロントエンド: http://localhost:5174
- バックエンドAPI: http://localhost:8000
- Nginx (本番模擬): http://localhost:8080
- Langfuse UI: http://localhost:3000
- PostgreSQL (アプリ): localhost:5435
- PostgreSQL (Langfuse): localhost:5436

### Langfuse初期アカウント
- Email: admin@local.dev
- Password: admin123
- API Public Key: pk-lf-local
- API Secret Key: sk-lf-local

## APIエンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/chat` | RAG対応チャット |
| POST | `/upload` | ドキュメントアップロード |
| GET | `/documents` | ドキュメント一覧 |
| POST | `/query` | ベクトル検索クエリ |
| POST | `/speech-to-text` | 音声→テキスト変換（スタブ） |
| GET | `/` | ヘルスチェック |

## コーディング規約

### Backend (Python)
- FastAPI + Pydantic による型安全なAPI設計
- シングルトンパターンでDB接続・ベクトルストア管理
- LangChainのローダーで各種ドキュメント形式に対応
- Azure OpenAI接続は `config.py` で一元管理

### Frontend (TypeScript/React)
- 関数コンポーネント + Hooks
- Tailwind CSSでスタイリング
- `services/api.ts`に全API呼び出しを集約

## データベース

### 接続情報 (開発環境)
```
Host: localhost:5435
Database: chat_db
User: chat_user
Password: chat_pass
```

## よく使うコマンド

```bash
# バックエンドのみ再起動
docker compose restart backend

# DBマイグレーション後の再起動
docker compose down -v && docker compose up -d

# ログをリアルタイム監視
docker compose logs -f

# コンテナに入る
docker compose exec backend bash
docker compose exec postgres psql -U chat_user -d chat_db
```

## 注意事項

1. **CORS設定**: 現在は全オリジン許可 (`*`) - 本番では制限が必要
2. **認証**: 現時点ではユーザー認証なし
3. **シークレット管理**: `.env`ファイルは必ず`.gitignore`に含める
4. **Langfuse**: 初期設定済み（pk-lf-local / sk-lf-local）、本番では変更が必要
