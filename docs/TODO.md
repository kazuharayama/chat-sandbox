# TODO

端末横断の残タスク。**ここには「未完了」だけ書く**。終わったら消す。
詳細な経緯は `git log` と `docs/reviews/` を参照。

**最終更新**: 2026-06-17

## いますぐ
- [ ] **動作確認** — `docker compose build backend` して起動し、下記を確認
  - `openai_compatible` プロバイダーでチャットできる
  - `EMBEDDING_PROVIDER` 切替が効く
  - ⚠️ `down -v` はDB・アップロード資産を全消しするので使うときだけ

## あとで（既知のギャップ）
- [ ] chunk_size / overlap のハードコード解消（管理画面から変更可に）
- [ ] ユーザー単位のデータ分離（セッション・ドキュメントをユーザーに紐付け）
- [ ] テスト整備（pytest / Vitest が現在ゼロ）

---
_直近完了 (2026-06-17): ローカルLLM汎用化（`openai_compatible` 追加）・命名整理・DBスキーマ一本化・doc-review 指摘のドキュメント整合。_
