# 要件定義書: chat-sandbox 全体ロードマップ

## 1. ドキュメント概要

| 項目 | 内容 |
|------|------|
| プロジェクト名 | chat-sandbox |
| 対象読者 | 開発者 |
| 作成日 | 2026-03-30 |
| 関連ドキュメント | [PRD](../PRD.md) |

## 2. 現状の実装状況

| ステップ | 状態 | 備考 |
|----------|------|------|
| Step 1: RAGの基本 | 完了 | レイヤードアーキテクチャ、Ollama、pgvector |
| Step 2: UX改善 | 完了 | SSEストリーミング、セッション管理、Gemini風UI |
| Step 3: マルチモーダル + Azure | 完了 | CLIP、Azure Blob Storage、Terraform |
| Step 4: エージェント設定基盤 | **完了** | DB動的読み込み、管理画面UI、Ollama/Claude CLI切替 |
| Step 5: 認証 | **完了** | Entra ID + MSAL + Terraform。全エンドポイント認証適用 |
| Step 5.5: 音声 (STT/TTS) | **完了** | Whisper (STT) + Piper (TTS)。マイクボタンUI |
| Step 5.5: タスク管理 | **完了** | カンバンボード (TODO/進行中/完了) |
| Step 5.5: Vision | **完了** | LLaVA等 (Ollama経由、画像base64送信) |
| Step 5.6: LLM刷新 | **完了** | Azure OpenAI廃止、Ollama一本化 + Claude CLI追加 |
| Step 6: マルチエージェント (FB) | **完了** | LangGraph Search Agent (Plan→Retrieve→Evaluate→Answer) |
| Step 7: 精度改善 (FE) | 未着手 | |

### 既知のギャップ

- chunk_size (1000) / chunk_overlap (200) がハードコード。管理画面から変更不可
- ユーザー単位のデータ分離が未実装 (セッション・ドキュメントのユーザー紐づけなし)
- テスト (pytest / Vitest) がゼロ

## 3. フィーチャー一覧

| ID | フィーチャー名 | 優先度 | 複雑度 | 依存 | 状態 | 詳細 |
|----|---------------|--------|--------|------|------|------|
| F0 | エージェント設定基盤の完成 | P0 (前提) | M | なし | **完了** | [F0-agent-config.md](F0-agent-config.md) |
| FA | Context Engineering Lab | P1 | L | F0 | **完了** | [FA-context-lab.md](FA-context-lab.md) |
| FB | Search Agent (Agentic RAG) | P2 | XL | F0, FA | **完了** | [FB-search-agent.md](FB-search-agent.md) |
| FC | 音声対話 (STT/TTS) | P2 | XL | なし | **完了** (Whisper+Piper) | [FC-voice.md](FC-voice.md) |
| FD | 認証統合 (Entra ID) | P1 | S | なし | **完了** | [FD-auth.md](FD-auth.md) |
| FE | 精度改善・運用基盤 | P2 | L | F0, FA | 未着手 | [FE-accuracy.md](FE-accuracy.md) |

**複雑度の目安**: S=数日, M=1週間, L=2-3週間, XL=3-4週間

## 4. 依存グラフ

```
FD (認証) ────────────────────────────┐
  [独立・並行可]                        │
                                       ▼
F0 (Step4完了) ──► FA (Context Lab) ──► FB (Search Agent)
                        │                    │
                        ▼                    │
                   FE (精度改善) ◄───────────┘

FC (Voice) ──────── [独立・いつでも着手可]
```

**判断根拠**:
- **F0が全ての前提**: ChatServiceがDB値を読まない限り、管理画面で設定を変更しても反映されない
- **FA→FB**: Search AgentのチューニングにContext Labのプレビュー機能が必要
- **FDは独立**: `core/auth.py` 実装済み + グレースフルスキップ付きで並行可能
- **FCは直交**: 既存アーキテクチャと独立しており、いつでも着手可

## 5. 実装フェーズ

### Phase 1: 基盤完成 (F0 + FD) — 並行実施可能

ChatServiceのDB動的読み込みを完成させ、管理画面の設定変更が実際に反映されるようにする。同時にEntra ID認証を統合する。

### Phase 2: Context Engineering Lab (FA)

RAGパイプラインのパラメータ調整・プレビュー・テスト実行ができる開発者向けツールを構築する。

### Phase 3: Search Agent + 精度改善 (FB + FE)

LangGraphベースのマルチステップ検索エージェントを実装し、評価指標による精度改善サイクルを確立する。

### Phase 4: 音声対話 (FC) — **完了**

音声入力→STT(Whisper)→RAGチャット→TTS(Piper)→音声出力のパイプラインをファイルベースで実装済み。
当初構想の WebRTC/リアルタイム化は採用せず、ブラウザ録音→HTTPアップロード方式で完結。詳細は [FC-voice.md](FC-voice.md)。

## 6. 全体API変更サマリ

| Feature | 新規API | 既存API変更 |
|---------|---------|-------------|
| F0 | `PUT /admin/models/{id}`, `PUT /admin/knowledge-sources/{id}` | なし |
| FA | `POST /admin/test-retrieval`, `POST /admin/test-chat`, `POST /admin/context-preview` | なし |
| FB | なし | `/chat/stream` に SSE type="step" 追加 |
| FC | `POST /speech-to-text`, `POST /text-to-speech` | なし |
| FD | なし | 全既存エンドポイントで認証が有効化 |
| FE | `POST /admin/evaluations/run`, `GET /admin/evaluations/results`, `POST /admin/evaluations/datasets` | なし |

## 7. 全体DB変更サマリ

| Feature | 新規テーブル | 既存テーブル変更 |
|---------|-------------|----------------|
| F0 | なし | なし |
| FA | なし | なし |
| FB | なし | seedデータ追加 |
| FC | なし (ステートレス) | なし |
| FD | なし | なし |
| FE | `evaluation_datasets`, `evaluation_results` | なし |

## 8. 将来検討事項

| 項目 | 現状 | 将来対応 |
|------|------|---------|
| シークレット管理 | `.env` ファイルで管理 | Azure Key Vault に移行。`DefaultAzureCredential` + `azure-keyvault-secrets` SDKで起動時取得。対象: `AZURE_STORAGE_CONNECTION_STRING`, `AZURE_CLIENT_SECRET`, `LANGFUSE_SECRET_KEY` |

## 9. リスク・留意事項

| リスク | 影響 | 対策 |
|--------|------|------|
| LangGraphのバージョン互換性 | FBの実装に影響 | バージョン固定 + 最小PoCを先に実装 |
| Piperバイナリ/日本語モデルの同梱 | FCのTTSが動作しない | コンテナに `piper` 実行ファイルとモデルを同梱、パスはconfig参照 |
| Whisperモデルサイズ vs 速度 | FCのSTT精度/レイテンシ | `whisper_model_size`で調整。GPU環境は `whisper_device=cuda` |
| LLMキャッシュ無効化タイミング | F0で設定変更が即反映されない | TTLキャッシュ (60s) + 手動クリアAPI |
| 評価データセットの作成コスト | FEの実用性 | 初期は小規模 (10-20 queries) で開始 |
