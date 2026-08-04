# Chat Sandbox - プロジェクトガイド

汎用マルチエージェントRAG基盤。ドキュメント（テキスト・画像）をアップロードし、ベクトル検索を活用してLLMが質問に回答する。エージェント設定・プロンプトはDB管理で、管理画面から変更可能。

## 実行環境（最初に読むこと）

- **開発しているこのマシンに GPU は無い（CPU のみ）。** GPU プロファイルをここで起動しない
- **GPU は別のリモートマシン（RTX 3090）にある。** 接続は SSH で、**リモートでの確認はユーザーが行う**
- ローカルで使うモデルは軽量なもの（`gemma2:2b`、`llama3.2:3b`）を前提にする

### 承認なしに実行しないこと

- `docker build` / `docker compose build` / `docker compose up --build` — **ユーザーの承認を取ってから**
- `ollama pull` / `docker pull` — サイズを伝えて承認を取る。事前に `df -h` で空き容量を確認
- `docker compose down -v` — **DB とアップロードした資産が全て消える。** スキーマ変更時のみ、承認を得てから

## アーキテクチャ概要

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐
│   Frontend  │────▶│   Backend   │────▶│     PostgreSQL      │
│  (React 19) │     │  (FastAPI)  │     │     (pgvector)      │
└─────────────┘     └─────────────┘     └─────────────────────┘
                          │
                    ┌─────┼──────────┐
                    ▼     ▼          ▼
             ┌──────────┐┌──────────┐
             │ Ollama   ││ Langfuse │
             │ (local)  ││(Tracing) │
             └──────────┘└──────────┘
```

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| Frontend | React 19, TypeScript, Vite 7, Tailwind CSS, lucide-react |
| Backend | Python 3.11, FastAPI, LangChain, Uvicorn |
| Database | PostgreSQL 16 + pgvector |
| LLM | Ollama / OpenAI互換サーバ (gemma2:2b / llama3.2:3b等、管理画面からプロバイダー・モデル変更可) |
| Embedding (テキスト) | Ollama nomic-embed-text |
| Embedding (画像) | CLIP ViT-B-32 (sentence-transformers) |
| Vision | LLaVA等 (Ollama経由、画像理解、base64送信) |
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
│   │   ├── tasks.py          # タスク管理 (カンバンボードCRUD)
│   │   └── speech.py         # 音声 (STT: Whisper, TTS: Piper)
│   ├── services/              # ビジネスロジック
│   │   ├── chat_service.py   # RAGチャット (DB動的読み込み)
│   │   ├── context_lab_service.py  # Context Lab (検索/コンテキスト/テスト)
│   │   ├── document_service.py     # ドキュメント処理
│   │   ├── speech_service.py       # STT (Whisper) + TTS (Piper)
│   │   └── llm_factory.py    # LLMプロバイダーファクトリ (Ollama/OpenAI互換)
│   ├── repositories/          # データアクセス
│   │   ├── vector_repository.py     # pgvector (テキスト)
│   │   ├── image_repository.py      # pgvector (CLIP画像)
│   │   ├── chat_repository.py       # チャット履歴
│   │   ├── task_repository.py       # タスク管理
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
│       │   ├── Chat.tsx       # チャット画面 (Vision対応、サイドバー開閉式、音声入力)
│       │   ├── Documents.tsx  # ドキュメント管理
│       │   ├── Tasks.tsx      # タスク管理 (カンバンボード)
│       │   ├── ContextLab.tsx # Context Lab (RAGパラメータ実験)
│       │   └── Admin.tsx      # 管理画面 (モデル/プロンプト/ナレッジソース)
│       ├── auth/
│       │   ├── msalConfig.ts  # MSAL設定 (Entra ID)
│       │   ├── AuthGuard.tsx  # 認証ガード (未設定時はスキップ)
│       │   └── useAuthSetup.ts # トークン自動取得hook
│       ├── hooks/
│       │   ├── useAudioRecorder.ts  # マイク録音 (WebM/MP4)
│       │   └── useAudioPlayer.ts    # TTS音声再生
│       ├── components/
│       │   ├── ChatWindow.tsx
│       │   ├── MessageInput.tsx
│       │   └── Sidebar.tsx
│       └── services/api.ts    # APIクライアント (全エンドポイント集約、Bearer自動付与)
├── docker/                     # Docker設定
├── docs/                       # ドキュメント
│   ├── PRD.md                 # プロダクト要件定義書
│   ├── requirements/          # 要件定義書 (F0〜FE)
│   ├── architecture-flow.md   # アーキテクチャ・フロー図 (Mermaid)
│   ├── feature-catalog.md     # 機能カタログ
│   └── er-diagram.md          # ER図 (Mermaid)
├── terraform/                  # インフラ (Azure)
│   ├── main.tf               # リソースグループ/Storage/Entra ID
│   ├── modules/
│   │   ├── storage/           # Azure Blob Storage
│   │   ├── vnet/              # VNet
│   │   └── entra_id/          # Entra IDアプリ登録+グループ
│   └── outputs.tf             # terraform output で .env 値を取得
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
- Azure CLI (`az login` 済み) — Terraform/Entra ID用 (オプション)

### 環境変数 (.env)
```bash
cp .env.example .env
# デフォルトでOllama使用、設定不要
```

### 起動コマンド
```bash
# 全サービス起動（Ollama CPU）
docker compose --profile cpu up -d

# ローカルLLM付き起動（GPU自動検出）
./scripts/start.sh

# GPU/CPU明示指定
./scripts/start.sh --gpu   # Ollama(GPU) + vLLM
./scripts/start.sh --cpu   # Ollama(CPU)のみ

# Ollamaモデルダウンロード（./scripts/start.sh で自動。手動の場合）
docker compose exec ollama-cpu ollama pull gemma2:2b
docker compose exec ollama-cpu ollama pull llama3.2:3b
docker compose exec ollama-cpu ollama pull nomic-embed-text

# 停止
docker compose down

# DB再作成（スキーマ変更時）  ⚠️ down -v は DB・アップロード資産を全消去する（「破壊的操作」節を参照）
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

### タスク管理
| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/tasks` | タスク一覧 (?status=todo でフィルタ可) |
| POST | `/tasks` | タスク作成 |
| PUT | `/tasks/{id}` | タスク更新 (タイトル/ステータス/並び順) |
| DELETE | `/tasks/{id}` | タスク削除 |

### 音声
| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/speech-to-text` | 音声ファイル → テキスト変換 (Whisper) |
| POST | `/text-to-speech` | テキスト → 音声合成 (Piper, WAV) |

### Context Lab
| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/admin/test-retrieval` | 検索プレビュー (チャンク+スコア) |
| POST | `/admin/context-preview` | コンテキストプレビュー (最終プロンプト全文) |
| POST | `/admin/test-chat` | テストチャット (SSEストリーミング) |

## LLMプロバイダー

管理画面の「LLMモデル」タブでプロバイダー・モデルを切り替え可能:

| プロバイダー | 実装 | 用途 | コスト |
|------------|------|------|--------|
| `ollama` | ChatOllama | LLM + Embedding | 無料 (ローカル) |
| `openai_compatible` | ChatOpenAI (`base_url`指定) | LLM (vLLM/llama.cpp/LM Studio/TGI/LocalAI/Ollama`/v1`等) | 無料〜従量 |

| モデル | プロバイダー | 用途 |
|--------|------------|------|
| `gemma2:2b` | ollama | チャット (デフォルト) |
| `llama3.2:3b` | ollama | チャット (代替モデル) |
| `nomic-embed-text` | ollama | テキストEmbedding |

新しいローカルLLMは `provider=openai_compatible` で `config.base_url`(例 `http://vllm:8000/v1`)を指定して管理画面から登録するだけ（コード変更不要）。`llm_factory.py` がプロバイダーに応じたインスタンスを生成。TTL 60秒キャッシュ付き。

Embedding はデフォルト Ollama だが、`EMBEDDING_PROVIDER=openai_compatible` で OpenAI 互換エンドポイントにも切り替え可能 (`vector_repository.py`)。

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
- React Router でURL遷移 (`/`, `/documents`, `/context-lab`, `/admin`)

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
- **タスク管理**: `tasks`
- **ベクトル系** (LangChain管理): `langchain_pg_collection`, `langchain_pg_embedding`
- **エージェント設定系**: `llm_models`, `agent_definitions`, `prompt_templates`, `agent_parameters`, `routing_rules`, `knowledge_sources`

詳細は `docs/er-diagram.md` を参照。

## 変更後の確認

変更が壊れていないかを機械が判定するための手順。「たぶん動く」で済ませず、これを実行して結果を見る。

```bash
# 1) 疎通スモーク（アプリ起動済みが前提: ./scripts/start.sh --cpu）
bash scripts/smoke.sh
#   成功 -> 最終行 "RESULT: OK"（終了コード 0）
#   失敗 -> 最終行 "RESULT: NG"（終了コード 1）。どの [CHECK] で落ちたかが出る
#   ※ chat 工程だけ Ollama + モデル(gemma2:2b) が必要

# 2) 単体テスト（LLM・DB 不要。ホストで走る）
cd backend && python3 -m pytest
#   成功 -> "1 passed"（緑 / 終了コード 0）
```

## 破壊的操作

- **`docker compose down -v`**: ボリュームごと削除するため **DB とアップロード資産（ドキュメント / チャット履歴）が全て消える**。本ファイル内では「起動コマンド」「よく使うコマンド」「注意事項」で通常手順のように登場するが、消える前提でのみ使うこと。
- **`ollama pull <model>`**: 実行前に `df -h` で空き容量を確認する。**4GB を超えるモデルは人間の承認を取る**（過去にディスクが 100% になり、PC 再起動と長時間の復旧を招いた事故がある）。

## よく使うコマンド

```bash
# バックエンドのみ再起動
docker compose restart backend

# DB再作成（スキーマ変更時）  ⚠️ down -v は DB・アップロード資産を全消去する（「破壊的操作」節を参照）
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
- [TODO](docs/TODO.md) — **今の作業対象はこれ**。`docs/PRD.md` と `docs/requirements/F0〜FE` は全体像であって、現在の優先順位ではない

## 注意事項

1. **CORS設定**: 現在は全オリジン許可 (`*`) — 本番では制限が必要
2. **認証**: Entra ID統合済み (MSAL + グループベース)。環境変数未設定時はグレースフルスキップ
3. **シークレット管理**: `.env` ファイルで管理。将来 Azure Key Vault に移行予定
4. **Langfuse**: 初期設定済み (pk-lf-local / sk-lf-local)、本番では変更が必要
5. **DBスキーマ変更時**: `docker compose down -v && docker compose up -d` が必要（⚠️ `down -v` は DB・アップロード資産を全消去。「破壊的操作」節を参照）
6. **Terraform**: `terraform apply` でEntra IDリソース作成 → `terraform output` で `.env` 値を取得
