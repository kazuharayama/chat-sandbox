# 残タスク (Remaining Tasks)

> このファイルは「今の未完了タスク」を端末横断で把握するための生きたボードです。
> 作業のたびに更新し、コミット＆プッシュします。完了したら ✅ にするか削除します。
> 詳細な根拠は各 doc-review レポート (`docs/reviews/`) を参照。

**最終更新**: 2026-06-17 / 直近の作業: doc-review 指摘のドキュメント整合を完了

---

## 🔧 運用・動作確認 (未実施)

- [ ] 依存追加 (`langchain-openai`) とスキーマ変更を反映して動作確認
  ```bash
  docker compose build backend
  docker compose down -v && docker compose --profile cpu up -d   # ※ down -v はDB/アップロード資産を破棄
  ```
  - `openai_compatible` プロバイダーでチャットできること
  - `EMBEDDING_PROVIDER` 切替が効くこと
  - `down -v` 後に `llm_models` が `provider`/`config` 形状で再作成され、シードが入ること

---

## ✅ ドキュメント整合 (doc-review 指摘) — 完了 (2026-06-17)

出典: `docs/reviews/2026-06-17-claude-opus-4-8.md`

- [x] FC-voice.md を Whisper+Piper にリメイク (WebRTC/aiortc/voice_sessions 削除)
- [x] PRD.md の Azure OpenAI 更新 (技術スタック/環境変数/Step1/Vision)
- [x] architecture-flow.md の Mermaid 図を Ollama/Claude CLI/CLIP に
- [x] F0-agent-config.md 冒頭注記を正確化 (3プロバイダー/現行モデル/vLLM→openai_compatible)
- [x] requirements/README.md Phase 4 を「完了(Whisper+Piper)」に、API/DB/リスク表のWebRTC残骸を除去、Key VaultからAZURE_OPENAI_API_KEY削除
- [x] agent-flow-chat-sandbox.md の Azure→Ollama 置換
- [x] er-diagram.md にエージェント設定テーブルのアプリ管理注記を追加
- [x] FE-accuracy.md の「GPT-4o Vision」→「Vision (LLaVA等, Ollama経由)」

> 備考: `F0-agent-config.md` 本文の azure_openai 疑似コードは冒頭注記で「実装当時のもの／現在非対応」と明示済みのため歴史的記述として保持。

---

## 📌 既知のギャップ (本機能とは別系統 / requirements/README.md より)

- [ ] `chunk_size`(1000) / `chunk_overlap`(200) がハードコード。管理画面から変更不可
- [ ] ユーザー単位のデータ分離が未実装 (セッション・ドキュメントのユーザー紐づけなし)
- [ ] テスト (pytest / Vitest) がゼロ
