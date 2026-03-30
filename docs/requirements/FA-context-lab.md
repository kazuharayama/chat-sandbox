# FA: Context Engineering Lab

| 項目 | 内容 |
|------|------|
| 優先度 | P1 |
| 複雑度 | L |
| 依存 | F0 |

## 1. 目的

RAGパイプラインのパラメータ (chunk_size, overlap, similarity_k, threshold, temperature, max_tokens) を管理画面から調整し、変更の効果をリアルタイムにプレビューできる開発者向けツールを提供する。

**コンテキストエンジニアリングの「実験→計測→改善」ループを回せる環境を作る。**

## 2. ユーザーストーリー

1. 開発者として、クエリを入力すると取得されるチャンクとスコアをプレビューできる (**Search Preview**)
2. 開発者として、パラメータを変更した状態でLLMに送信される最終プロンプト全文をプレビューできる (**Context Preview**)
3. 開発者として、一時的なパラメータオーバーライドでサンドボックスチャットを実行し、本番設定に影響を与えずに結果を確認できる (**Test Execution**)
4. 開発者として、similarity_kやthresholdを変更すると、取得チャンク数やスコア分布がどう変わるかを並べて比較できる (**比較モード**)

## 3. 受入基準

1. `/admin/test-retrieval` にqueryとparametersをPOSTすると、取得チャンク + スコア一覧が返ること
2. `/admin/test-chat` にqueryとparameter overridesをPOSTすると、override済みパラメータでLLM応答が返ること (本番設定は変わらない)
3. Context Previewでsystem prompt + RAG context + history + user messageの全文が表示されること
4. テスト実行の結果がLangfuseにtraceとして記録されること (metadata: `test=true`)
5. UI上でsimilarity_k=3とsimilarity_k=5の結果を並べて比較できること

## 4. 技術アプローチ

### 4.1 バックエンド

**新規: `backend/services/context_lab_service.py`**
- `test_retrieval(query, params)`: `VectorRepository.similarity_search_with_score()` をparams.similarity_kで呼び出し、チャンク + スコアを返却
- `test_chat(query, params)`: 一時的なLLMインスタンスをparamsのtemperature/max_tokensで生成し、ChatServiceと同等のロジックで応答を取得
- `build_context_preview(query, params)`: `_build_messages()` のロジックを呼んでmessages配列を返却 (LLMは呼ばない)

**新規: `backend/routers/context_lab.py`**
- `POST /admin/test-retrieval`
- `POST /admin/test-chat`
- `POST /admin/context-preview`

**既存: `backend/repositories/vector_repository.py`**
- `similarity_search_with_score()` は既に存在 (44-45行目)
- thresholdによるフィルタリングを追加するラッパーが必要

### 4.2 フロントエンド

**新規: `frontend/src/pages/ContextLab.tsx`**
- 3ペインレイアウト:
  - 左: パラメータフォーム (similarity_k, threshold, temperature, max_tokens)
  - 中央: 検索結果プレビュー / コンテキストプレビュー
  - 右: テストチャット応答
- パラメータフォーム: similarity_k (slider 1-20)、threshold (slider 0.0-1.0)、temperature (slider 0.0-2.0)、max_tokens (number)
- 検索プレビュー: チャンク一覧 with スコアバー表示
- コンテキストプレビュー: 最終プロンプトのシンタックスハイライト表示
- テスト実行: SSEストリーミングでの応答表示
- 比較モード: 2つのパラメータセットの結果を横並び表示

**`frontend/src/App.tsx`**:
- ルーティング追加: `/admin/context-lab` → ContextLab

## 5. API変更

| メソッド | パス | リクエスト | レスポンス |
|---------|------|----------|----------|
| POST | `/admin/test-retrieval` | `{query, similarity_k, threshold, collection_name}` | `{chunks: [{content, score, metadata}]}` |
| POST | `/admin/test-chat` | `{query, similarity_k, threshold, temperature, max_tokens, system_prompt_override?}` | SSEストリーム |
| POST | `/admin/context-preview` | `{query, similarity_k, threshold}` | `{messages: [{role, content}]}` |

## 6. DB変更

なし (既存テーブルで対応可能)

## 7. リスク・留意事項

- **テスト実行のコスト**: test-chatは毎回LLMを呼ぶため、APIコストに注意。UIにコスト目安を表示することを検討
- **比較モードの同時リクエスト**: 2つのパラメータセットで同時にtest-retrievalを呼ぶため、バックエンドの並行処理能力に依存
