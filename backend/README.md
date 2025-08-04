# LangChain RAGシステム

このプロジェクトは、LangChainを使用したシンプルなRAG（Retrieval Augmented Generation）システムです。

## セットアップ

1. 必要なパッケージをインストールします:
```bash
pip install -r requirements.txt
```

2. `.env`ファイルを作成し、必要なAPIキーを設定します:
```
OPENAI_API_KEY=your_openai_api_key

# Langfuse Settings (LLMトレーシング・可視化)
LANGFUSE_HOST=http://localhost:3000
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
```

**Langfuse統合について:**
- LangfuseはLLMアプリケーションのトレーシングと可視化を提供します
- ローカルでLangfuseを起動している場合（`http://localhost:3000`）、上記の設定でトレースが自動的に送信されます
- Langfuseダッシュボードで、LLMの実行ログ、パフォーマンス、コストを分析できます

3. アプリケーションを起動します:
```bash
uvicorn app:app --reload
```

## 機能

### ドキュメント管理機能
- ドキュメントのアップロード (`/upload` エンドポイント)
- ドキュメント一覧の取得 (`/documents` エンドポイント)
- PDF、テキスト、Markdown、CSVなど複数のフォーマットに対応

### ベクトルストア管理
- FAISSを使用したベクトルストアの作成と保存
- アプリ起動時の自動ロード
- ドキュメントアップロード時の自動更新

### 質問応答機能
- RAGを使った質問応答 (`/query` エンドポイント)
- 通常の質問応答（RAGを使わないオプション）
- 情報源の表示

### チャット機能
- RAGを使ったチャット応答 (`/chat` エンドポイント)
- 添付ファイル対応（画像など）
- 情報源の表示

### LLMトレーシング・可視化（Langfuse統合）
- 全てのLLM実行が自動的にトレースされます
- Langfuseダッシュボードでリアルタイム監視
- パフォーマンス分析とコスト追跡
- プロンプトエンジニアリングとデバッグ支援

## Docker環境での実行

このアプリケーションはDocker環境で実行することも可能です。詳細はプロジェクトルートの`docker-compose.yml`を参照してください。
