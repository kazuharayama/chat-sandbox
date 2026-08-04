# 起動手順書（全パターン）

このアプリの起動方法と、それぞれで「実際に何が起きるか」を全パターンまとめる。

## 前提（仕組み）

- backend が LLM / Embedding で見に行く宛先は `LLM_BASE_URL`（Embedding は `EMBEDDING_BASE_URL` 未設定なら `LLM_BASE_URL` を流用）。
- ローカルLLMは Docker Compose のプロファイルで起動する:
  - `cpu` プロファイル → `ollama-cpu`（ホスト名 `ollama-cpu:11434`）
  - `gpu` プロファイル → `ollama-gpu`（ホスト名 `ollama-gpu:11434`）＋ `vllm`（`vllm:8000` / ホスト側 `:8001`）
- backend の既定 `LLM_BASE_URL` は `http://ollama-cpu:11434`。
- **`scripts/start.sh` を使うと、選んだプロファイルに合わせて `LLM_BASE_URL` を自動設定する**（GPU→`ollama-gpu`、CPU→`ollama-cpu`）。生の `docker compose` では自動設定されない点に注意。

---

## 推奨: `scripts/start.sh`（LLM_BASE_URL を自動整合）

| コマンド | 起動 | LLM_BASE_URL | チャット/Embedding | 用途 |
|---|---|---|---|---|
| `./scripts/start.sh` | GPU自動検出 → gpu or cpu | 検出結果に自動整合 | ✅ 動く | 通常はこれ |
| `./scripts/start.sh --gpu` | `ollama-gpu` + `vllm` | `http://ollama-gpu:11434` | ✅ 動く | GPUを明示 |
| `./scripts/start.sh --cpu` | `ollama-cpu` | `http://ollama-cpu:11434` | ✅ 動く | CPUを明示 |
| `./scripts/start.sh --no-llm` | ローカルLLM無し | 既定のまま | ⚠️ 別途設定が必要 | 外部/OpenAI互換前提 |

- `start.sh` は起動後に必要なモデル（`gemma2:2b` / `llama3.2:3b` / `nomic-embed-text`）を自動 pull する。
- GPU検出条件: `nvidia-smi` が使える ＋ Docker に nvidia ランタイムがある。どちらか欠けると CPU にフォールバック。

---

## 生の `docker compose`（手動。LLM_BASE_URL は自動整合されない）

| コマンド | 起動するLLM系 | backendの宛先(既定) | チャット/Embedding | 備考 |
|---|---|---|---|---|
| `docker compose up -d` | **なし** | `ollama-cpu` | ❌ 繋がらない | ローカルLLMを起動しない（外部前提） |
| `docker compose --profile cpu up -d` | `ollama-cpu` | `ollama-cpu` | ✅ 動く | モデルは手動 pull が必要 |
| `docker compose --profile gpu up -d` | `ollama-gpu` + `vllm` | `ollama-cpu` | ❌ **既定だと壊れる** | 下記の対処が必要 |

### GPU を生 compose で使うときの対処

`docker compose --profile gpu` は `ollama-gpu` を起動するが、backend の既定は `ollama-cpu` を見るため繋がらない。`.env` に次を設定する（または `start.sh --gpu` を使う）:

```bash
LLM_BASE_URL=http://ollama-gpu:11434
```

モデルの手動 pull（cpu 例）:

```bash
docker compose exec ollama-cpu ollama pull gemma2:2b
docker compose exec ollama-cpu ollama pull llama3.2:3b
docker compose exec ollama-cpu ollama pull nomic-embed-text
```

---

## OpenAI互換 / 外部LLM を使う場合

ローカル Ollama ではなく OpenAI 互換サーバ（vLLM / llama.cpp / LM Studio / 外部エンドポイント）を使う場合:

1. **チャット用モデル**: 管理画面でモデルを追加し、`provider=openai_compatible`、`config.base_url` にエンドポイント（例 `http://vllm:8000/v1`）を設定する。GPU の面倒はそのサーバ側の話で、`start.sh` の GPU 検出とは無関係。
2. **Embedding**: 既定は Ollama（`nomic-embed-text`）。OpenAI 互換の埋め込みに寄せる場合は環境変数で切り替える:

   ```bash
   EMBEDDING_PROVIDER=openai_compatible
   EMBEDDING_BASE_URL=http://<embedding-server>/v1
   ```

   切り替えない場合は、**Embedding 用に Ollama を動かしておく必要がある**（LLM を外部にしても Embedding だけは Ollama が要る点に注意）。

---

## まとめ（迷ったら）

- **ローカルLLMで手早く動かす** → `./scripts/start.sh`（GPU/CPU 自動、宛先も自動整合）。
- **生 compose で GPU** → `.env` に `LLM_BASE_URL=http://ollama-gpu:11434` を忘れずに。
- **外部/OpenAI互換** → モデルを管理画面で `openai_compatible` 登録。Embedding の宛先も忘れずに設定。

## アクセスURL（起動後）

- フロントエンド: <http://localhost:5174>
- バックエンドAPI: <http://localhost:8000>
- Nginx: <http://localhost:8080>
- Langfuse: <http://localhost:3000>
- Ollama: <http://localhost:11434>（LLMプロファイル起動時）
- vLLM: <http://localhost:8001>（gpu プロファイル時）
