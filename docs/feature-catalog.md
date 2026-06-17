# 機能カタログ: chat-sandbox

> 汎用マルチエージェントRAG基盤の機能一覧

## 凡例

- 実装済み
- 一部実装
- 未実装 (計画中)

---

## 1. チャット

| 機能 | 状態 | 説明 |
|------|------|------|
| RAGチャット | 実装済み | アップロード済みドキュメントを参照して回答を生成 |
| SSEストリーミング | 実装済み | トークン単位でリアルタイム応答表示 |
| 会話コンテキスト引き継ぎ | 実装済み | 直近20件のメッセージをプロンプトに含める |
| ソース表示 | 実装済み | 回答の参照元ドキュメントをバッジ表示 |
| チャットからファイルアップロード | 実装済み | チャット画面で直接ファイルを添付して質問 |
| 多言語対応 | 実装済み | 応答言語の切り替え (デフォルト: 日本語) |
| Vision画像理解 | 実装済み | LLaVA等のVisionモデルで画像をbase64送信・理解 |
| 音声入力 (STT) | 実装済み | マイクボタンでWhisperによる音声認識 → テキスト変換 |
| 音声出力 (TTS) | 実装済み | Piperによるテキスト → 音声合成 (日本語) |
| 検索エージェント (Agentic RAG) | 実装済み | LangGraph: Plan → Retrieve → Evaluate → Answer のマルチステップ検索 |
| Supervisor ルーティング | 実装済み | 質問内容から `search` / `chat` エージェントを自動振り分け |

## 2. セッション管理

| 機能 | 状態 | 説明 |
|------|------|------|
| セッション作成・一覧 | 実装済み | 会話をセッション単位で管理 |
| セッション削除 | 実装済み | 不要な会話を削除 (メッセージも連動削除) |
| タイトル自動設定 | 実装済み | 最初のメッセージからセッションタイトルを自動生成 |
| サイドバー (開閉式) | 実装済み | Gemini風のセッション切り替えUI。開閉ボタン付き |

## 3. ドキュメント管理

| 機能 | 状態 | 説明 |
|------|------|------|
| ドキュメントアップロード | 実装済み | PDF, TXT, Markdown, CSV, 画像 (PNG/JPG等) に対応 |
| Azure Blob Storage永続化 | 実装済み | アップロードファイルをBlob Storageに保存 |
| テキストベクトル化 | 実装済み | LangChainローダー → チャンキング (1000/200) → Ollama nomic-embed-text → pgvector |
| 画像ベクトル化 (CLIP) | 実装済み | CLIP ViT-B-32でマルチモーダル検索対応 |
| ドキュメント削除 | 実装済み | Blob Storage + ベクトルストアの両方から削除 |
| グリッド/リスト表示切替 | 実装済み | ドキュメント一覧の表示モード切り替え |
| 定期バッチベクトル化 | 未実装 | Blob Storageの新規ファイルを自動ベクトル化 |

## 4. タスク管理

| 機能 | 状態 | 説明 |
|------|------|------|
| カンバンボード | 実装済み | TODO / 進行中 / 完了 の3カラム |
| タスクCRUD | 実装済み | 作成・編集・削除 |
| ドラッグ&ドロップ | 実装済み | カラム間のステータス変更 |

## 5. エージェント設定

| 機能 | 状態 | 説明 |
|------|------|------|
| エージェント定義 (DB) | 実装済み | エージェントの名前・種別・モデル紐づけをDBで管理 |
| プロンプト管理 (DB) | 実装済み | バージョン管理 + ロールバック対応 |
| パラメータ管理 (DB) | 実装済み | エージェントごとのパラメータをkey-valueで管理 |
| ルーティングルール (DB) | 実装済み | 条件プロンプトに基づくエージェント選択ルール |
| 知識ソース管理 (DB) | 実装済み | コレクション名・similarity_k等のベクトル検索設定 |
| 管理API (CRUD) | 実装済み | `/admin/*` エンドポイントで全設定の読み書き |
| 管理画面 (プロンプト編集) | 実装済み | プロンプトの編集・バージョン履歴・ロールバックUI |
| 管理画面 (モデル編集) | 実装済み | temperature, max_tokensの編集。デフォルトモデル切り替え |
| 管理画面 (モデル追加) | 実装済み | プロバイダー選択 (Ollama / Claude CLI) + パラメータ設定 |
| 管理画面 (ナレッジソース編集) | 実装済み | similarity_kのスライダー編集 |
| ChatServiceのDB動的読み込み | 実装済み | LLMパラメータ・similarity_kをDBから読み込み。TTL 60秒キャッシュ |
| LLMキャッシュクリア | 実装済み | `/admin/cache/clear` で手動キャッシュクリア |

## 6. LLMプロバイダー

| 機能 | 状態 | 説明 |
|------|------|------|
| Ollama (ローカルLLM) | 実装済み | gemma2:2b / llama3.2:3b 等。GPU/CPU両対応。デフォルトプロバイダー |
| OpenAI互換サーバ | 実装済み | `provider=openai_compatible` で vLLM/llama.cpp/LM Studio/TGI/LocalAI 等を `base_url` 指定で利用 (ChatOpenAI) |
| Embedding (テキスト) | 実装済み | nomic-embed-text でベクトル化。`EMBEDDING_PROVIDER` で Ollama / OpenAI互換 を切り替え |
| Claude CLI (`claude -p`) | 実装済み | LangChain BaseChatModel ラッパー (ChatClaudeCLI)。Teams契約内で利用 |
| LLMプロバイダー切り替え | 実装済み | 管理画面から Ollama / OpenAI互換 / Claude CLI を切り替え |
| GPU自動検出 | 実装済み | `scripts/start.sh` でGPU有無を検出し、docker compose profilesで切り替え |
| LLMファクトリ | 実装済み | `llm_factory.py` でproviderに応じたインスタンス生成。TTLキャッシュ付き |

## 7. コンテキストエンジニアリング

| 機能 | 状態 | 説明 |
|------|------|------|
| Context Lab (検索プレビュー) | 実装済み | クエリに対する取得チャンク + スコアをプレビュー |
| Context Lab (コンテキストプレビュー) | 実装済み | LLMに渡される最終プロンプト全文を表示 |
| Context Lab (テスト実行) | 実装済み | パラメータを一時上書きしてSSEストリーミングでテスト |
| Context Lab (比較モード) | 未実装 | 2つのパラメータセットの結果を横並び比較 |
| 評価指標 (Recall@k, MRR) | 未実装 | 評価データセットによる検索精度の定量評価 |
| チャンク戦略の実験 | 未実装 | chunk_size/overlapの組み合わせ別に精度比較 |

## 8. 監視・トレーシング

| 機能 | 状態 | 説明 |
|------|------|------|
| Langfuse統合 | 実装済み | LLM呼び出しの自動トレーシング |
| Langfuse UI | 実装済み | セルフホスト (localhost:3000) でトレース確認 |
| コスト・レイテンシ可視化 | 未実装 | Langfuseダッシュボードでの運用モニタリング |

## 9. 認証・セキュリティ

| 機能 | 状態 | 説明 |
|------|------|------|
| Entra ID トークン検証 | 実装済み | `core/auth.py` でJWT検証。グレースフルスキップ付き |
| グループベースアクセス制御 | 実装済み | 全エンドポイントに `require_group_member` 適用 |
| 管理画面のアクセス制限 | 実装済み | adminグループによる `/admin/*` の `require_admin` 保護 |
| フロントエンド MSAL統合 | 実装済み | AuthGuard + トークン自動取得 + Bearer自動付与 |
| Terraform Entra ID | 実装済み | アプリ登録・グループ・シークレットを自動プロビジョニング |
| ユーザー単位のデータ分離 | 未実装 | セッション・ドキュメントのユーザー紐づけ |

## 10. インフラ

| 機能 | 状態 | 説明 |
|------|------|------|
| Docker Compose (全サービス) | 実装済み | `docker compose up` でアプリ + Langfuse一式起動 |
| Terraform (Azure Storage) | 実装済み | Storage Accountのプロビジョニング |
| Terraform (Entra ID) | 実装済み | アプリ登録 + セキュリティグループの自動作成 |
| Nginx リバースプロキシ | 実装済み | 本番模擬 (localhost:8080) |
| Docker Compose profiles (GPU/CPU) | 実装済み | `--profile gpu` / `--profile cpu` でOllama/vLLM切り替え |
| GPU自動検出スクリプト | 実装済み | `scripts/start.sh` でnvidia-smi + Dockerランタイム検出 |
| Swagger UI | 実装済み | FastAPI標準 (localhost:8000/docs) |
| Azure Key Vault統合 | 将来検討 | 現在は `.env` で管理。本番ではKey Vaultに移行予定 |

---

## アーキテクチャ

詳細は [architecture-flow.md](architecture-flow.md) を参照。

```
Frontend (React 19) → Backend (FastAPI) → PostgreSQL (pgvector)
                            │
                    ┌───────┼───────┐
                    ▼       ▼       ▼
            Ollama / Claude CLI  Blob  Langfuse
```

## 関連ドキュメント

- [PRD (プロダクト要件定義書)](PRD.md)
- [要件定義書 (ロードマップ)](requirements/README.md)
- [アーキテクチャ・フロー図](architecture-flow.md)
- [ER図](er-diagram.md)
