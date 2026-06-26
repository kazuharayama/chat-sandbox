# F0: エージェント設定基盤の完成

| 項目 | 内容 |
|------|------|
| 優先度 | P0 (前提) |
| 複雑度 | M |
| 依存 | なし |
| 状態 | **完了** |

> **更新 (2026-06-17)**: Azure OpenAI を廃止し、現在は **`ollama` / `openai_compatible` / `claude_cli`** の3プロバイダー構成 (`backend/services/llm_factory.py`)。
> デフォルトモデルは **`gemma2:2b`** (代替 `llama3.2:3b`)、高品質用に Claude CLI (`claude -p`)。
> 本文中の "azure_openai" / "gpt-4o" / "vllm" 記述は実装当時のもので**現在は対応しない**。
> vLLM/llama.cpp/LM Studio 等の OpenAI 互換サーバは `provider=openai_compatible` + `config.base_url`(例 `http://vllm:8000/v1`) で扱う (コード変更不要)。

## 1. 目的

ChatServiceがDBのエージェント設定 (LLMパラメータ、knowledge_sourcesのsimilarity_k等) を実際に使用するようにする。管理画面でモデル・ナレッジソースも編集可能にする。**Azure OpenAIとローカルLLM (Ollama) を管理画面から切り替えられるようにする。**

**現状の問題**:
- 管理画面でパラメータを変更しても、ChatServiceがハードコード値を使用しているため反映されない
- `AzureChatOpenAI` がハードコードされており、他のLLMプロバイダーを使えない
- `llm_models` テーブルがAzure OpenAI前提のカラム設計になっている

## 2. ユーザーストーリー

1. 管理者として、管理画面でLLMのtemperature/max_tokensを変更すると、次のチャットからその値が反映される
2. 管理者として、knowledge_sourcesのsimilarity_kを管理画面で変更できる
3. 管理者として、管理画面でモデル一覧・ナレッジソース一覧を編集できる
4. **管理者として、管理画面でチャットに使うLLMをAzure OpenAI / Ollama から切り替えられる**
5. **管理者として、Ollamaで利用可能なモデル (llama3.1, gemma2等) を選択できる**
6. **開発者として、新しいLLMプロバイダーを追加する際に、既存コードへの影響が最小限で済む**

## 3. 受入基準

1. ChatServiceがLLMインスタンス生成時に `llm_models` テーブルのtemperature/max_tokensを使用すること
2. `ChatService._retrieve()` が `knowledge_sources.config.similarity_k` を使用すること
3. 管理画面でLLMモデルのtemperature/max_tokensを編集・保存できること
4. 管理画面でknowledge_sourcesのsimilarity_k/thresholdを編集・保存できること
5. 設定変更後、再起動なしで次のリクエストから反映されること
6. **`llm_models` テーブルの `provider` カラムに基づいて、Azure OpenAI / Ollama のLLMインスタンスが生成されること**
7. **管理画面でデフォルトモデルを切り替えると、次のチャットから切り替わること**
8. **Ollamaが起動していない場合、エラーメッセージが返り、Azure OpenAIにフォールバックしないこと (明示的な切り替えを尊重)**

## 4. 技術アプローチ

### 4.1 LLMプロバイダー切り替え設計

```
llm_models テーブル
├── gpt-4o         → provider: "azure_openai"  → AzureChatOpenAI
├── llama3.1:8b    → provider: "ollama"         → ChatOllama
└── gemma2:9b      → provider: "ollama"         → ChatOllama
```

**LLMファクトリパターン**: providerに応じたLangChainインスタンスを生成する関数を用意。

```python
# backend/services/llm_factory.py
def create_llm(model: LLMModelInfo, settings: Settings) -> BaseChatModel:
    if model.provider == "azure_openai":
        return AzureChatOpenAI(
            azure_deployment=model.deployment_name,
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=model.config.get("api_version", "2024-08-01-preview"),
            temperature=model.temperature,
            max_tokens=model.max_tokens,
            streaming=True,
        )
    elif model.provider == "ollama":
        return ChatOllama(
            model=model.deployment_name,  # e.g. "llama3.1:8b"
            base_url=model.config.get("base_url", "http://ollama:11434"),
            temperature=model.temperature,
            num_predict=model.max_tokens,
        )
    elif model.provider == "vllm":
        return ChatOpenAI(
            model=model.deployment_name,  # e.g. "meta-llama/Llama-3.1-8B-Instruct"
            base_url=model.config.get("base_url", "http://vllm:8000/v1"),
            api_key="dummy",  # vLLM doesn't require a real key
            temperature=model.temperature,
            max_tokens=model.max_tokens,
            streaming=True,
        )
    else:
        raise ValueError(f"Unknown provider: {model.provider}")
```

### 4.2 バックエンド変更

**新規: `backend/services/llm_factory.py`**
- `create_llm(model, settings)` — プロバイダーに応じたLangChain LLMインスタンスを生成

**`backend/services/chat_service.py`**:
- `__init__` でLLMをハードコード初期化する代わりに、リクエストごと (TTL 60秒キャッシュ付き) で `agent_config_repo.get_default_model()` → `llm_factory.create_llm()` でインスタンスを生成
- `_retrieve()` で `agent_config_repo.list_knowledge_sources()` から `similarity_k` を読み込み

**`backend/routers/admin.py`**:
- `PUT /admin/models/{model_id}` エンドポイント追加
- `POST /admin/models` エンドポイント追加 (新規モデル登録)
- `PUT /admin/knowledge-sources/{source_id}` エンドポイント追加

**`backend/repositories/agent_config_repository.py`**:
- `update_model()` メソッド追加
- `create_model()` メソッド追加
- `update_knowledge_source()` メソッド追加

### 4.3 Docker Compose変更

### 4.3 Docker Compose + GPU/CPU プロファイル

`docker compose --profile gpu up` / `docker compose --profile cpu up` で切り替え。

**`docker-compose.yml`**:
```yaml
# --- ローカルLLM (GPU環境) ---
ollama-gpu:
  image: ollama/ollama
  profiles: ["gpu"]
  ports:
    - "11434:11434"
  volumes:
    - ollama_data:/root/.ollama
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]

vllm:
  image: vllm/vllm-openai
  profiles: ["gpu"]
  ports:
    - "8001:8000"
  environment:
    - MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
  volumes:
    - vllm_cache:/root/.cache/huggingface

# --- ローカルLLM (CPU環境) ---
ollama-cpu:
  image: ollama/ollama
  profiles: ["cpu"]
  ports:
    - "11434:11434"
  volumes:
    - ollama_data:/root/.ollama
  # GPU設定なし。CPU推論 (低速だが動作する)
```

**新規: `scripts/start.sh`** — GPU自動検出 + 適切なプロファイルで起動:
```bash
#!/bin/bash
# GPU検出: nvidia-smi が使えるか + Docker GPU ランタイムがあるか
if command -v nvidia-smi &>/dev/null && docker info 2>/dev/null | grep -q "nvidia"; then
  echo "GPU detected. Starting with GPU profile..."
  docker compose --profile gpu up -d
else
  echo "No GPU detected. Starting with CPU profile..."
  docker compose --profile cpu up -d
fi
```

> **ポイント**:
> - `nvidia-smi` の存在だけでなく、Docker の GPU ランタイム対応もチェック
> - vLLM は GPU 必須のため `gpu` プロファイルにのみ配置
> - Ollama は GPU/CPU 両方で動作するが、GPU 環境では GPU 版を優先
> - プロファイルなしの `docker compose up` では既存サービス (frontend, backend, postgres等) のみ起動し、ローカルLLMは起動しない

### 4.4 フロントエンド変更

**`frontend/src/pages/Admin.tsx`**:
- モデル一覧セクションに編集ボタン追加 (provider, deployment_name, temperature, max_tokensフォーム)
- モデル追加ボタン (プロバイダー選択 → Azure OpenAI / Ollama)
- デフォルトモデル切り替えボタン (is_default トグル)
- ナレッジソースセクションに編集ボタン追加 (similarity_k, thresholdフォーム)
- 直接 `fetch` → `apiService` 経由にリファクタ

**`frontend/src/services/api.ts`**:
- admin系APIメソッド追加 (listAgents, createModel, updateModel, updateKnowledgeSource等)

## 5. API変更

| メソッド | パス | リクエスト | レスポンス |
|---------|------|----------|----------|
| POST | `/admin/models` | `{name, provider, deployment_name, temperature, max_tokens, config}` | 作成されたモデル情報 |
| PUT | `/admin/models/{model_id}` | `{temperature, max_tokens, is_default, config}` | 更新後のモデル情報 |
| PUT | `/admin/knowledge-sources/{source_id}` | `{config: {similarity_k, threshold}}` | 更新後のソース情報 |

## 6. DB変更

### llm_models テーブル変更

既存カラムをプロバイダー非依存に再設計:

```sql
ALTER TABLE llm_models
  ADD COLUMN provider VARCHAR(50) NOT NULL DEFAULT 'azure_openai',
  ADD COLUMN config JSONB DEFAULT '{}';
  -- endpoint_env_var, api_key_env_var, api_version は config JSONB に移行
```

**provider別のconfigスキーマ**:

| provider | config内容 |
|---------|-----------|
| `azure_openai` | `{"api_version": "2024-08-01-preview", "endpoint_env_var": "AZURE_OPENAI_ENDPOINT", "api_key_env_var": "AZURE_OPENAI_API_KEY"}` |
| `ollama` | `{"base_url": "http://ollama:11434"}` |
| `vllm` | `{"base_url": "http://vllm:8000/v1"}` |

### seedデータ

```sql
-- Azure OpenAI (既存)
INSERT INTO llm_models (name, provider, deployment_name, temperature, is_default, config)
VALUES ('gpt-4o', 'azure_openai', 'gpt-4o', 0.7, true,
  '{"api_version": "2024-08-01-preview"}');

-- Ollama (新規)
INSERT INTO llm_models (name, provider, deployment_name, temperature, config)
VALUES ('llama3.1:8b', 'ollama', 'llama3.1:8b', 0.7,
  '{"base_url": "http://ollama:11434"}');

-- vLLM (新規、GPU環境のみ)
INSERT INTO llm_models (name, provider, deployment_name, temperature, config)
VALUES ('llama3.1-vllm', 'vllm', 'meta-llama/Llama-3.1-8B-Instruct', 0.7,
  '{"base_url": "http://vllm:8000/v1"}');
```

## 7. 依存ライブラリ追加

```
langchain-ollama>=0.2.0
langchain-openai>=0.2.0   # vLLM用 (OpenAI互換APIで接続)
```

## 8. リスク・留意事項

- **キャッシュ戦略**: リクエストごとにDB問い合わせは非効率。TTL付きキャッシュ (60秒) を設け、手動キャッシュクリアAPIも用意する
- **LLMインスタンス再生成**: モデル切り替え時にインスタンスを再生成する必要がある。キャッシュキーにmodel_idを含めることで、同一モデルの再生成を避ける
- **Ollamaモデルの初回ダウンロード**: `ollama pull llama3.1:8b` が必要。初回起動時に自動pullするスクリプトを用意するか、手順をドキュメント化する
- **GPU未搭載環境**: OllamaはCPUでも動作するが応答速度が大幅に低下。vLLMはGPU必須で `cpu` プロファイルでは起動しない
- **ストリーミング互換性**: `ChatOllama`, `ChatOpenAI` (vLLM) ともにLangChainの `astream()` に対応。既存のSSEストリーミングコードはそのまま動作する
- **DBマイグレーション**: 既存の `endpoint_env_var`, `api_key_env_var`, `api_version` カラムから `provider` + `config` への移行スクリプトが必要
- **vLLMのモデルダウンロード**: 初回起動時にHuggingFaceからモデルをダウンロードする (数GB〜数十GB)。`vllm_cache` ボリュームでキャッシュし再ダウンロードを防止
- **Docker GPU ランタイム**: GPU利用にはホストに `nvidia-container-toolkit` のインストールが必要。`scripts/start.sh` でチェックし、未インストール時はガイドメッセージを表示
