# PRD: 汎用マルチエージェントRAG基盤

## 1. 概要

cmos-maintenance-appのバックエンド構成問題を踏まえ、ベストプラクティスで再構築する汎用マルチエージェント基盤。
ドキュメント（テキスト・画像）をアップロードし、ベクトル検索を活用してLLMが質問に回答する。
エージェント設定・プロンプトはDB管理で、管理画面から変更可能。

## 2. 目的

- **汎用的なRAG + マルチエージェント基盤を作る**
- cmos-maintenance-appの機能を設定ベースで再現可能にする
- エージェント定義・プロンプト・ルーティングをDB管理にし、コード変更なしで挙動を変えられるようにする
- レイヤードアーキテクチャのリファレンス実装

## 3. スコープ

### 対象
- ローカル開発環境（Docker Compose）+ Azure リソース（Blob Storage）
- Entra ID によるグループベース認証（予定）
- 段階的に機能を追加

### 対象外（将来検討）
- Azure Container Apps へのデプロイ
- グラフRAG（Apache AGE）

## 4. 技術スタック

| レイヤー | 技術 |
|---------|------|
| Frontend | React 19, TypeScript, Vite 7, Tailwind CSS |
| Backend | Python 3.11, FastAPI, LangChain |
| Database | PostgreSQL 16 + pgvector |
| LLM | Azure OpenAI gpt-4o（AzureChatOpenAI, SSEストリーミング） |
| Embedding (テキスト) | Azure OpenAI text-embedding-ada-002 |
| Embedding (画像) | CLIP ViT-B-32（sentence-transformers） |
| ファイル保存 | Azure Blob Storage |
| 監視 | Langfuse v3（セルフホスト、docker-compose統合） |
| インフラ | Docker Compose + Terraform (Azure) |
| アーキテクチャ | レイヤードアーキテクチャ + DI（FastAPI Depends） |

## 5. アーキテクチャ

### バックエンド構成

```
backend/
├── main.py                 # エントリポイント（薄い）
├── core/                   # 設定・DI・ログ
│   ├── config.py          # Pydantic Settings
│   ├── dependencies.py    # FastAPI Depends
│   └── logging.py
├── models/                 # Pydanticスキーマ
├── routers/                # HTTPハンドラ（薄い）
├── services/               # ビジネスロジック
├── repositories/           # データアクセス（DB, Blob, pgvector）
└── infrastructure/         # 外部サービス接続（CLIP等）
```

### 依存の方向
```
routers → services → repositories → infrastructure
                ↑
            core/config（全層から参照可）
```

## 6. 環境変数

```bash
# Azure OpenAI
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_ENDPOINT=<endpoint>
AZURE_OPENAI_API_VERSION=2024-08-01-preview
AZURE_OPENAI_LLM_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Azure Blob Storage（terraform output -raw storage_connection_string）
AZURE_STORAGE_CONNECTION_STRING=<connection_string>
AZURE_STORAGE_CONTAINER_NAME=documents

# Langfuse
LANGFUSE_PUBLIC_KEY=pk-lf-local
LANGFUSE_SECRET_KEY=sk-lf-local
```

## 7. システム構成

```
docker-compose
├── frontend        (React 19)              :5174
├── backend         (FastAPI)               :8000
├── postgres        (pgvector)              :5435
├── nginx           (リバースプロキシ)       :8080
├── langfuse-web    (Langfuse UI)           :3000
├── langfuse-worker (Langfuse Worker)
├── clickhouse      (Langfuse OLAP)
├── redis           (Langfuse Cache)
└── minio           (Langfuse Storage)

Azure
├── Resource Group: rg-chat-sandbox
├── Storage Account: chatsandboxdocs
│   └── Container: documents
└── (予定) Entra ID App Registration
```

## 8. 実装ステップ

### Step 1: RAGの基本 ✅ 完了
- [x] レイヤードアーキテクチャ導入
- [x] Azure OpenAI (gpt-4o) でチャット応答
- [x] ドキュメントアップロード → チャンキング → Embedding → pgvector
- [x] ベクトル検索 → RAGチャット動作
- [x] ドキュメント削除API（Blob + ベクトル両方）
- [x] フロントエンドでソース（参照元）表示

### Step 2: UX改善 ✅ 完了
- [x] ストリーミング応答（SSE）
- [x] チャット履歴のDB永続化
- [x] チャット履歴のSidebar + セッション管理
- [x] 会話の文脈引き継ぎ（直近20件をプロンプトに含める）
- [x] Gemini風UIデザイン
- [x] チャットからファイルアップロード

### Step 3: マルチモーダル + Azure連携 ✅ 完了
- [x] CLIP による画像ベクトル化
- [x] Azure Blob Storage でドキュメント永続化
- [x] Terraform でAzure Storage Account プロビジョニング
- [x] ドキュメント一覧のグリッド/リスト切り替え

### Step 4: エージェント設定基盤 ✅ DB設計 + 管理API完了
- [x] エージェント設定DBテーブル設計・実装
  - llm_models, agent_definitions, prompt_templates, agent_parameters, routing_rules, knowledge_sources
- [x] プロンプトのバージョン管理 + ロールバック
- [x] 管理API（/admin/*）
- [ ] 管理画面フロントエンド
- [ ] ChatServiceがDBからプロンプトを動的読み込み

### Step 5: 認証・セキュリティ（予定）
- [ ] Entra IDセキュリティグループ作成
- [ ] アプリ登録 + トークンにグループ情報含める
- [ ] バックエンド: トークン検証 + グループチェック
- [ ] フロントエンド: MSAL でログイン + トークン付与

### Step 6: マルチエージェント（予定）
- [ ] 汎用エージェントランナー（DBから設定読み込み → LangGraphでグラフ動的構築）
- [ ] Supervisor → 子エージェントのルーティング
- [ ] 検索エージェント（Plan → Retrieve → Evaluate → Answerループ）
- [ ] ナレッジグラフ（Apache AGE）統合

### Step 7: 精度改善・運用（予定）
- [ ] チャンクサイズ・オーバーラップの調整
- [ ] Langfuseでトレース確認・コスト把握
- [ ] Blob Storageの定期ベクトル化バッチ
- [ ] GPT-4o Vision による画像内容理解

## 9. API設計

| メソッド | パス | 説明 | 状態 |
|---------|------|------|------|
| GET | `/` | ヘルスチェック | 実装済み |
| POST | `/chat` | RAGチャット | 実装済み |
| POST | `/chat/stream` | RAGチャット（SSE） | 実装済み |
| POST | `/upload` | ドキュメントアップロード | 実装済み |
| GET | `/documents` | ドキュメント一覧 | 実装済み |
| DELETE | `/documents/{id}` | ドキュメント削除 | 実装済み |
| POST | `/sessions` | セッション作成 | 実装済み |
| GET | `/sessions` | セッション一覧 | 実装済み |
| GET | `/sessions/{id}/messages` | メッセージ取得 | 実装済み |
| DELETE | `/sessions/{id}` | セッション削除 | 実装済み |
| GET | `/admin/agents` | エージェント一覧 | 実装済み |
| GET | `/admin/agents/{id}/prompts` | プロンプト取得 | 実装済み |
| PUT | `/admin/prompts/{id}/{key}` | プロンプト更新 | 実装済み |
| GET | `/admin/prompts/{id}/{key}/versions` | バージョン履歴 | 実装済み |
| POST | `/admin/prompts/{id}/{key}/rollback/{ver}` | ロールバック | 実装済み |
| GET | `/admin/models` | LLMモデル一覧 | 実装済み |
| GET | `/admin/knowledge-sources` | 知識ソース一覧 | 実装済み |
| GET | `/admin/routing-rules` | ルーティングルール一覧 | 実装済み |

## 10. データモデル

### PostgreSQL テーブル

**チャット履歴**
- `chat_sessions` — セッション管理（タイトル自動設定）
- `chat_messages` — メッセージ保存（role, content, sources）

**ベクトルデータ（LangChain自動生成）**
- `langchain_pg_collection` — コレクションメタデータ
- `langchain_pg_embedding` — ベクトル埋め込み（chat_documents / image_documents）

**エージェント設定**
- `llm_models` — LLMモデル定義（deployment, temperature, max_tokens）
- `agent_definitions` — エージェント定義（name, type, model）
- `prompt_templates` — プロンプト（バージョン管理、ロールバック対応）
- `agent_parameters` — パラメータ（max_revisions, similarity_k等）
- `routing_rules` — ルーティング条件（condition_prompt, routes）
- `knowledge_sources` — 知識ソース設定（collection, similarity_k, threshold）

### 接続情報（開発環境）
```
Host: localhost:5435
Database: chat_db
User: chat_user
Password: chat_pass
```

## 11. 非機能要件

| 項目 | 要件 |
|------|------|
| 開発環境 | `docker compose up` のみで全サービス起動 |
| レスポンス | SSEストリーミングで体感即応答 |
| データ永続化 | PostgreSQL + Azure Blob Storage |
| 設定変更 | 管理APIでプロンプト・パラメータ変更（再デプロイ不要） |
| 言語 | UIは日本語 |

## 12. 関連ドキュメント

- [エージェントフロー図 (chat-sandbox)](agent-flow-chat-sandbox.md)
- [エージェントフロー図 (cmos-maintenance)](agent-flow-cmos-maintenance.md)
- [Entra ID認証セットアップ手順](entra-id-setup.md)
