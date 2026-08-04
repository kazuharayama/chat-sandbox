# TODO

端末横断の残タスク。**ここには「未完了」だけ書く**。終わったら消す。
詳細な経緯は `git log` と `docs/reviews/` を参照。
実行環境・承認が必要な操作は `CLAUDE.md` の冒頭「実行環境」を参照（**このマシンに GPU は無い**）。

## ゴール

最終目標はループエンジニアリング（AI が自走して開発を回す仕組みを作る）。
土台としてハーネス → コンテキスト → プロンプト エンジニアリングが必要。
まず成否を機械が返す道具（`scripts/smoke.sh` / pytest = ハーネス）を固める。
個別タスクは、これに近づくかで優先順位づけする。

**最終更新**: 2026-08-04

## いますぐ

- [ ] **backend が起動できない（最優先ブロッカー / smoke.sh で判明）**
  - 症状: backend が `import langchain_ollama` でクラッシュ → アプリ全体が起動しない。`bash scripts/smoke.sh` は `RESULT: NG (backend unreachable)` を返す
  - 原因1: 現 backend イメージが **4ヶ月前**のもので langchain 0.1.x、**`langchain-ollama` が入っていない**（`requirements.txt` は langchain>=0.3.0 / langchain-ollama>=0.2.0 を要求）
  - 原因2: **再ビルドが失敗する** — `docker/backend/Dockerfile` の Piper モデル取得 URL が **HTTP 404**（HuggingFace `.../ja_JP/amitaro/medium/ja_JP-amitaro-medium.onnx`）。`wget` が exit 8 で止まる
  - 次の手順: ① Dockerfile の Piper 取得 URL を正しいものに直す（or 取得失敗を致命化しない）→ ② **再ビルド（ビルドは承認必須）** → ③ `bash scripts/smoke.sh` が `RESULT: OK` になるか確認
- [ ] **動作確認** — `openai_compatible` プロバイダーでチャット / `EMBEDDING_PROVIDER` 切替（アプリが起動できてから）

## あとで（既知のギャップ）

- [ ] chunk_size / overlap のハードコード解消（管理画面から変更可に）
- [ ] ユーザー単位のデータ分離（セッション・ドキュメントをユーザーに紐付け）
- [ ] `CLAUDE.md` から腐る記述を削る — ディレクトリ構成・API一覧は実装から読めるため必ずズレる。直近の「docs を実装に整合」コミット群の発生源
- [ ] Vitest 整備（フロントエンド）

## やらないこと

- **GitHub Actions / CI を作らない** — ローカル LLM 前提のアプリなので噛み合わない。判定はこのマシンの中で完結させる
- **ドキュメントを増やさない** — 変更は既存ファイルに足す
- **未確認の値を書かない** — エンドポイント・ポート・環境変数名は grep して実物を見てから書く
- **報告を「たぶん動きます」で終わらせない** — 実行したコマンドと実際の出力を示す

---
_直近完了 (2026-08-04): pytest 導入（`backend/pytest.ini`・`conftest.py`・`tests/test_models.py`、1本 green）・`scripts/smoke.sh` 作成・CLAUDE.md に「実行環境」「変更後の確認」「破壊的操作」節を追加。_

_直近完了 (2026-06-17): ローカルLLM汎用化（`openai_compatible` 追加）・命名整理・DBスキーマ一本化・doc-review 指摘のドキュメント整合。_
