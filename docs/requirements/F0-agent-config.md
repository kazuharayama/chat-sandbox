# F0: エージェント設定

| 項目 | 内容 |
|------|------|
| 優先度 | P0 (前提) |
| 複雑度 | M |
| 依存 | なし |

## 1. 目的

エージェントの設定 — 使用するLLMプロバイダー/モデル、生成パラメータ、プロンプト、検索パラメータ (similarity_k 等) — を DB で一元管理し、管理画面から変更できるようにする。コードを変更せずに、使用するLLM (Ollama / OpenAI互換サーバ) の切り替えや検索挙動の調整ができ、変更が次のチャットに反映される状態にする。

## 2. ユーザーストーリー

1. 管理者として、応答の生成パラメータ（温度・最大長など）を管理画面から調整したい。再デプロイせず応答の傾向を変えられるように。
2. 管理者として、検索の挙動（取得件数など）を管理画面から調整したい。回答の根拠の集め方をチューニングできるように。
3. 管理者として、チャットに使うLLM（プロバイダー・モデル）を管理画面から選び・切り替えたい。用途やコストで使い分けられるように。
4. 開発者として、新しいLLMプロバイダー/モデルを設定の追加だけで導入したい。コード改修なしに選択肢を増やせるように。

## 3. 受入基準

1. チャット応答が、DBのモデル設定の生成パラメータ（温度・最大長）に従って生成されること
2. 検索時に、DBの検索設定（取得件数 similarity_k 等）が使われること
3. 管理画面でモデルの生成パラメータを編集・保存できること
4. 管理画面で検索設定（取得件数・しきい値）を編集・保存できること
5. 設定変更（生成パラメータ・デフォルトモデルの切り替えを含む）が、再起動なしで次のリクエストから反映されること
6. モデルに設定された provider（ollama / openai_compatible）に応じたLLMで応答が生成されること
7. 選択中のプロバイダーが利用不可のとき、他プロバイダーに暗黙で切り替えず、エラーを返すこと

## 4. 技術アプローチ

### 4.1 LLMプロバイダーの抽象化

- provider の値に応じて LangChain のチャットモデルを生成するファクトリを1箇所に設ける。
- provider は2種類とする: `ollama`（ローカル・ネイティブAPI）/ `openai_compatible`（OpenAI互換APIを持つサーバ全般）。
- vLLM / llama.cpp / LM Studio / TGI / LocalAI などの OpenAI 互換サーバは、個別実装せず `openai_compatible` の1種類で扱う。新しいサーバの追加はモデル登録のみで済み、コード変更を要しない。
- 接続先（base_url 等）とモデル名は、モデル定義の設定値として与える。

### 4.2 ローカルLLMの起動（GPU / CPU）

- ローカルLLM（Ollama / vLLM 等）は Docker Compose のプロファイル（`gpu` / `cpu`）で起動構成を切り替える。
- 起動スクリプトが GPU の有無を判定し、適切なプロファイルで起動する。
- vLLM のような GPU 前提のサーバは `gpu` プロファイルにのみ含める。

## 5. API変更

| メソッド | パス | リクエスト | レスポンス |
|---------|------|----------|----------|
| POST | `/admin/models` | `{name, provider, deployment_name, temperature, max_tokens, config}` | 作成されたモデル情報 |
| PUT | `/admin/models/{model_id}` | `{temperature, max_tokens, is_default, config}` | 更新後のモデル情報 |
| PUT | `/admin/knowledge-sources/{source_id}` | `{config: {similarity_k, threshold}}` | 更新後のソース情報 |

## 6. DB変更

### llm_models（モデル定義）

プロバイダー非依存の設計にする。主なフィールド:

- `provider`: `ollama` / `openai_compatible`
- `config`(JSONB): プロバイダー固有の接続情報（base_url、必要なら api_key）
- 生成パラメータ（temperature / max_tokens）、`deployment_name`（モデル名）、`is_default`

接続情報はすべて `config` に集約し、Azure 専用だった旧カラム（endpoint / api_key / api_version）は持たない。

provider ごとの `config` の形:

| provider | config |
|------|------|
| `ollama` | `{ base_url }` |
| `openai_compatible` | `{ base_url, api_key }`（vLLM/llama.cpp/LM Studio/TGI/LocalAI） |

### 初期データ（seed）

起動時に初期モデルを投入する（既定モデル1件 + 代替）。具体的なモデル名・接続先の値は環境設定に従い、本書には固定値を書かない。

## 7. 依存ライブラリ

- `langchain-ollama`（Ollama 連携）
- `langchain-openai`（OpenAI 互換サーバへの接続に使用）

## 8. リスク・留意事項

- 設定反映のタイミング: モデルインスタンスを短期キャッシュするため、変更が即座に反映されない場合がある。手動クリアまたは短いTTLで「次のリクエストから反映」を担保する。
- ローカルLLMの初回モデル取得: 対象モデルを事前に取得（pull）する必要がある。起動時の自動取得または手順のドキュメント化で対応する。
- GPU / CPU: Ollama は CPU でも動くが低速。vLLM は GPU 必須で `cpu` プロファイルでは起動しない。GPU 利用にはホストに NVIDIA Container Toolkit が必要。
- ストリーミング互換性: いずれのプロバイダーも逐次ストリーミングに対応し、既存の SSE 応答はそのまま動作する。
