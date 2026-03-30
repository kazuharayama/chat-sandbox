# FB: Search Agent (Agentic RAG)

| 項目 | 内容 |
|------|------|
| 優先度 | P2 |
| 複雑度 | XL |
| 依存 | F0, FA |

## 1. 目的

単純な「クエリ → ベクトル検索 → 回答」の1パスRAGを、**Plan → Retrieve → Evaluate → (Re-retrieve) → Answer** のマルチステップエージェントに進化させる。LangGraphでグラフを動的に構築し、supervisorがルーティングする。

## 2. ユーザーストーリー

1. ユーザーとして、複雑な質問 (例: 「AとBの違いは?」) をすると、エージェントが内部でクエリを分解して複数回検索し、包括的な回答を得られる
2. ユーザーとして、初回検索で十分な情報が得られなかった場合、エージェントがクエリを書き換えて再検索してくれる
3. 管理者として、エージェントの検索ステップ数や判断基準を管理画面から設定変更できる
4. 開発者として、Langfuseで各ステップ (Plan/Retrieve/Evaluate/Answer) のトレースを確認できる

## 3. 受入基準

1. LangGraph StateGraphでノード (plan, retrieve, evaluate, answer) が定義され、条件付きエッジで接続されていること
2. evaluateノードが検索結果の十分性を判定し、不十分ならretrieveに戻ること (最大リトライ回数は `agent_parameters` で設定可能)
3. planノードがクエリ分解を行い、複数のサブクエリを生成できること
4. supervisorエージェントが `routing_rules` テーブルに基づいて子エージェント (search_agent, direct_chat等) をルーティングすること
5. 各ステップがLangfuseにspanとして記録されること
6. 既存の1パスRAGチャットも引き続き動作すること (agent_type="chat" のフォールバック)

## 4. 技術アプローチ

### 4.1 新規依存関係

```
langgraph>=0.2.0
```

### 4.2 バックエンド

**新規: `backend/services/search_agent.py`**
- LangGraph StateGraphの定義
- State: `{query, sub_queries, retrieved_docs, evaluation_result, answer, iteration_count}`
- Nodes: `plan_node`, `retrieve_node`, `evaluate_node`, `answer_node`
- Conditional edges: evaluate → retrieve (insufficient) / evaluate → answer (sufficient)
- `max_iterations` は `agent_parameters` テーブルから読み込み

**新規: `backend/services/supervisor.py`**
- `routing_rules` テーブルからルール読み込み
- LLMに condition_prompt を渡してルーティング判定
- ルーティング先: search_agent / direct_chat / etc.

**変更: `backend/services/chat_service.py`**
- `chat_stream()` の先頭でsupervisorを呼び、agent_typeに応じて処理を分岐
- agent_type="search" なら search_agent に委譲
- agent_type="chat" なら従来のパスを維持

**変更: `backend/repositories/agent_config_repository.py`**
- seedデータに search_agent の定義 + prompt_templates + parameters を追加

### 4.3 SSEイベント拡張

既存の `/chat/stream` に `type="step"` イベントを追加:

```json
{"type": "step", "step": "plan", "detail": "クエリを3つのサブクエリに分解しました"}
{"type": "step", "step": "retrieve", "detail": "5件のチャンクを取得しました"}
{"type": "step", "step": "evaluate", "detail": "追加検索が必要です"}
{"type": "step", "step": "retrieve", "detail": "3件の追加チャンクを取得しました"}
{"type": "step", "step": "evaluate", "detail": "十分な情報が揃いました"}
{"type": "token", "content": "..."}
```

### 4.4 フロントエンド

**変更: `frontend/src/components/ChatWindow.tsx`**
- `type="step"` イベントの表示 (ステップインジケーター: Plan → Retrieve → Evaluate → Answer)

## 5. API変更

| メソッド | パス | 変更内容 |
|---------|------|---------|
| POST | `/chat/stream` | SSEに `type="step"` イベント追加 (既存イベントに追加) |

## 6. DB変更

既存テーブルへの **seedデータ追加**:

| テーブル | 追加内容 |
|---------|---------|
| `agent_definitions` | search_agent, supervisor エージェント |
| `prompt_templates` | plan/evaluate/answer用プロンプト |
| `agent_parameters` | max_iterations, min_relevance_score等 |
| `routing_rules` | supervisor → search_agent/assistant ルール |

## 7. リスク・留意事項

- **LangGraphバージョン互換性**: バージョンを固定し、最小PoCを先に実装して検証する
- **ループの無限回避**: max_iterationsを必ず設定し、evaluateノードでカウンターチェックを行う
- **レイテンシ**: マルチステップになるため応答時間が増加する。SSEのstepイベントでユーザーに進捗を伝えることで体感を改善
- **フォールバック**: supervisorが判定できない場合は従来の1パスRAGにフォールバック
