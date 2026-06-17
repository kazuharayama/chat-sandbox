# 残タスク (Remaining Tasks)

> このファイルは「今の未完了タスク」を端末横断で把握するための生きたボードです。
> 作業のたびに更新し、コミット＆プッシュします。完了したら ✅ にするか削除します。
> 詳細な根拠は各 doc-review レポート (`docs/reviews/`) を参照。

**最終更新**: 2026-06-17 / 対象コミット: `b1eead1`

---

## 🔧 運用・動作確認

- [ ] 依存追加 (`langchain-openai`) とスキーマ変更を反映して動作確認
  ```bash
  docker compose build backend
  docker compose down -v && docker compose --profile cpu up -d
  ```
  - `openai_compatible` プロバイダーでチャットできること
  - `EMBEDDING_PROVIDER` 切替が効くこと
  - `down -v` 後に `llm_models` が `provider`/`config` 形状で再作成され、シードが入ること

---

## 🔴 Blocker (ドキュメント整合 / doc-review 優先度1)

出典: `docs/reviews/2026-06-17-claude-opus-4-8.md`

- [ ] **FC-voice.md を Whisper+Piper にリメイク** — 現状は WebRTC+aiortc+Azure Speech の架空仕様。`/speech-to-text` `/text-to-speech` に合わせ、`voice_sessions`/`voice_events`/aiortc 記述を削除
- [ ] **PRD.md の Azure OpenAI 更新** — `PRD.md:34-35,70-75,111`。技術スタック/環境変数を Ollama + Claude CLI + `LLM_BASE_URL`系へ
- [ ] **architecture-flow.md の Mermaid 図更新** — `:112-113,148,227` の Azure OpenAI を Ollama/Claude CLI/CLIP へ

## 🟡 High (doc-review 優先度2)

- [ ] **F0-agent-config.md の vLLM 記載を `openai_compatible` へ書き換え** — 疑似コード/configスキーマ/seed例 (`:74-82,216,231-234`)
- [ ] **モデル名の統一** — doc の `llama3.1:8b`/`gemma2:9b` → 実シード `gemma2:2b`/`llama3.2:3b`
- [ ] **requirements/README.md Phase 4 整理** — WebRTC前提の Phase4 を削除/将来構想化し、FC を「完了(Whisper+Piper)」で統一

## 🟢 Low (doc-review 優先度3)

- [ ] **ER図補完** — `knowledge_sources.is_enabled` 追記、routing_rules リレーション、"agent-configはアプリ起動時に `_ensure_tables()` で作成" の注記
- [ ] **agent-flow-chat-sandbox.md の Azure→Ollama 置換** (`:11,32`)

---

## 📌 既知のギャップ (本機能とは別系統 / requirements/README.md より)

- [ ] `chunk_size`(1000) / `chunk_overlap`(200) がハードコード。管理画面から変更不可
- [ ] ユーザー単位のデータ分離が未実装 (セッション・ドキュメントのユーザー紐づけなし)
- [ ] テスト (pytest / Vitest) がゼロ
