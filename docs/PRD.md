# PRD: RAGチャットアプリケーション（学習用）

## 1. 概要

RAG（Retrieval Augmented Generation）アプリ開発のスキルを習得するための学習用プロジェクト。
ドキュメントをアップロードし、ベクトル検索＋ナレッジグラフを活用してLLMが質問に回答する。

## 2. 目的

- **ひとりでRAGアプリを作れるようになる**
- ベクトル検索（pgvector）とグラフRAG（Apache AGE）の両方を学ぶ
- LLMトレーシング（Langfuse）でRAGの挙動を可視化・改善する手法を身につける

## 3. スコープ

### 対象
- ローカル開発環境（Docker Compose）で完結
- シングルユーザー（自分用）
- 段階的に機能を追加して学びを深める

### 対象外（将来検討）
- クラウドデプロイ
- マルチユーザー・認証

## 4. 技術スタック

| レイヤー | 技術 |
|---------|------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS |
| Backend | Python 3.11, FastAPI, LangChain |
| Database | PostgreSQL 16 + pgvector + Apache AGE |
| LLM | Azure OpenAI gpt-4o（AzureChatOpenAI経由） |
| Embedding | Azure OpenAI text-embedding-ada-002 |
| 監視 | Langfuse v3（セルフホスト、docker-compose統合） |
| インフラ | Docker Compose |

## 5. 環境変数

```bash
# Azure OpenAI（cmos-maintenance-appのterraform outputから取得）
AZURE_OPENAI_API_KEY=<terraform output -raw openai_primary_key>
AZURE_OPENAI_ENDPOINT=<terraform output -raw openai_endpoint>
AZURE_OPENAI_API_VERSION=2024-08-01-preview
AZURE_OPENAI_LLM_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Langfuse（docker-compose内で自動設定済み）
LANGFUSE_PUBLIC_KEY=pk-lf-local
LANGFUSE_SECRET_KEY=sk-lf-local
```

## 6. システム構成

```
docker-compose
├── frontend        (React 19)              :5174
├── backend         (FastAPI)               :8000
├── postgres        (pgvector + AGE)        :5435
├── nginx           (リバースプロキシ)        :8080
├── langfuse-web    (Langfuse UI)           :3000
├── langfuse-worker (Langfuse Worker)
├── clickhouse      (Langfuse OLAP)
├── redis           (Langfuse Cache)
└── minio           (Langfuse Storage)
```

## 7. 学習ステップ

### Step 1: RAGの基本（まずここを動かす）
**学ぶこと**: ドキュメント → チャンキング → Embedding → ベクトル検索 → LLM応答

- [x] Terraformコード削除
- [x] LLMバックエンドをAzure OpenAI (gpt-4o) に切替
- [x] 不要な依存関係の整理
- [x] Langfuseをdocker-composeに統合
- [ ] 全サービスが正常に起動する
- [ ] ドキュメントアップロード → RAGチャットが動作する
- [ ] ドキュメント削除API実装
- [ ] フロントエンドでソース（参照元）表示

### Step 2: 精度改善
**学ぶこと**: チャンク戦略、検索パラメータ調整、プロンプト改善

- [ ] チャンクサイズ・オーバーラップの調整と効果比較
- [ ] k値（検索件数）の調整
- [ ] プロンプトテンプレートの改善
- [ ] Langfuseでトレース確認・コスト把握

### Step 3: グラフRAG
**学ぶこと**: ナレッジグラフの構築、Cypherクエリ、グラフ＋ベクトルのハイブリッド検索

- [ ] Apache AGEでナレッジグラフ構築
- [ ] ドキュメントからエンティティ・関係を自動抽出
- [ ] Cypherクエリによるグラフ検索
- [ ] ベクトル検索＋グラフ検索のハイブリッドRAG

### Step 4: UX改善
**学ぶこと**: ストリーミング、チャット履歴、UI

- [ ] ストリーミング応答（SSE）
- [ ] チャット履歴のDB永続化
- [ ] チャット履歴のSidebar接続
- [ ] UIのブラッシュアップ

## 8. API設計

| メソッド | パス | 説明 | 状態 |
|---------|------|------|------|
| GET | `/` | ヘルスチェック | 実装済み |
| POST | `/chat` | RAGチャット | 実装済み |
| POST | `/upload` | ドキュメントアップロード | 実装済み |
| GET | `/documents` | ドキュメント一覧 | 実装済み |
| DELETE | `/documents/{id}` | ドキュメント削除 | 要実装 |
| POST | `/query` | ベクトル検索 | 実装済み |

## 9. データモデル

### PostgreSQL テーブル

#### langchain_pg_collection（既存・自動生成）
- ベクトルコレクションのメタデータ

#### langchain_pg_embedding（既存・自動生成）
- ドキュメントチャンクのベクトル埋め込み

#### Apache AGE グラフ（Step 3で構築）
- エンティティ（ノード）とリレーション（エッジ）のナレッジグラフ

#### chat_sessions（Step 4で追加）
- チャット履歴の永続化用

### 接続情報（開発環境）
```
Host: localhost:5435
Database: chat_db
User: chat_user
Password: chat_pass
```

## 10. 非機能要件

| 項目 | 要件 |
|------|------|
| 開発環境 | `docker compose up` のみで全サービス起動 |
| レスポンス | チャット応答は30秒以内 |
| データ永続化 | PostgreSQLボリュームで永続化 |
| 言語 | UIは日本語 |
