# FE: 精度改善・運用基盤

| 項目 | 内容 |
|------|------|
| 優先度 | P2 |
| 複雑度 | L |
| 依存 | F0, FA |

## 1. 目的

RAGの精度を定量的に評価し改善するための指標・ツールを導入する。運用可視化をLangfuseで強化する。

## 2. ユーザーストーリー

1. 開発者として、チャンクサイズ/オーバーラップの組み合わせ別に検索精度を比較できる
2. 開発者として、Recall@k / MRRの数値を見て検索品質を評価できる
3. 開発者として、LangfuseでLLMコスト・レイテンシを確認できる
4. 管理者として、新しいドキュメントがアップロードされると自動的にベクトル化される
5. 開発者として、GPT-4o Visionで画像の内容を理解した上で検索結果に含められる

## 3. 受入基準

1. 評価データセット (query + expected_docs) を投入し、Recall@k, MRRを自動計算できること
2. chunk_size/overlapの異なる設定でのベクトル化を並行実行できること (比較用コレクション)
3. Langfuseのダッシュボードでtrace数、平均レイテンシ、累積コストが確認できること
4. Blob Storageへの新規アップロードがバッチジョブでベクトル化されること
5. 画像アップロード時にGPT-4o Visionで内容説明テキストが生成され、テキスト埋め込みとしても検索可能になること

## 4. 技術アプローチ

### 4.1 バックエンド

**新規: `backend/services/evaluation_service.py`**
- Recall@k: 正解ドキュメントが上位k件に含まれる割合
- MRR: 正解ドキュメントの順位の逆数の平均
- 評価データセットの管理 (JSON / DB)

**新規: `backend/services/batch_vectorizer.py`**
- Blob Storageの新規/更新ファイルを定期チェック
- DocumentServiceのチャンキング + ベクトル化パイプラインを呼び出し
- 実行方式: APScheduler (docker-composeにワーカー追加を検討)

**変更: `backend/services/document_service.py`**
- chunk_size / overlapをパラメータ化 (現在はハードコード: chunk_size=1000, overlap=200)
- GPT-4o Visionによる画像内容テキスト生成の統合

**新規: `backend/routers/evaluation.py`**
- `POST /admin/evaluations/run`
- `GET /admin/evaluations/results`
- `POST /admin/evaluations/datasets`

### 4.2 フロントエンド

**Context Lab (FA) に統合**:
- 評価データセット登録UI
- 評価実行ボタン + 結果表示 (Recall@k, MRRのグラフ)
- パラメータ別の精度比較テーブル

## 5. API変更

| メソッド | パス | リクエスト | レスポンス |
|---------|------|----------|----------|
| POST | `/admin/evaluations/run` | `{dataset_id, parameters}` | `{result_id}` |
| GET | `/admin/evaluations/results` | query: `?dataset_id=xxx` | `[{parameters, recall_at_k, mrr, details}]` |
| POST | `/admin/evaluations/datasets` | `{name, queries: [{query, expected_doc_ids}]}` | `{dataset_id}` |

## 6. DB変更

### evaluation_datasets

```sql
CREATE TABLE evaluation_datasets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    queries JSONB NOT NULL,  -- [{query, expected_doc_ids}]
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### evaluation_results

```sql
CREATE TABLE evaluation_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dataset_id UUID REFERENCES evaluation_datasets(id),
    parameters JSONB NOT NULL,  -- {similarity_k, chunk_size, overlap, ...}
    recall_at_k FLOAT,
    mrr FLOAT,
    details JSONB,  -- per-query results
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## 7. リスク・留意事項

- **評価データセットの作成コスト**: 初期は手動で小規模データセット (10-20 queries) を作成。LLMで自動生成する仕組みは将来検討
- **バッチベクトル化の重複実行**: 同じドキュメントを複数回ベクトル化しないように、処理済みフラグまたはハッシュチェックが必要
- **GPT-4o Visionのコスト**: 画像あたりのAPI呼び出しコストが高い。バッチ処理で制御する
