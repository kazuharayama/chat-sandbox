from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.agents import AgentExecutor, create_openai_tools_agent
from typing import Dict, List, Any, TypedDict, Annotated, Sequence
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import asyncio
import uuid
from dotenv import load_dotenv
import os

# LangGraphのインポート
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

# 環境変数の読み込み
load_dotenv()

# APIキーの確認
if not os.getenv("OPENAI_API_KEY"):
    print("警告: OPENAI_API_KEYが設定されていません。.envファイルに設定してください。")

app = FastAPI(title="LangGraph マルチエージェントオーケストレーションアプリ")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では特定のオリジンに制限することをお勧めします
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket接続を管理するためのクラス
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_message(self, client_id: str, message: str, sender: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json({
                "sender": sender,
                "message": message
            })

manager = ConnectionManager()

# グローバル変数として現在のclient_idを保持
current_client_id = None

# 状態の型定義
class AgentState(TypedDict):
    query: str
    research_result: str
    planning_result: str
    implementation_result: str
    feedback: str
    final_result: str
    current_agent: str
    needs_revision: bool

# リサーチエージェント用のツール
@tool
def search_information(query: str) -> str:
    """特定のトピックに関する情報を検索します。"""
    # 実際のアプリケーションではWebAPIや検索エンジンを使用します
    return f"「{query}」に関する情報: これは検索結果のシミュレーションです。実際のアプリケーションでは外部APIを使用します。"

@tool
def analyze_data(data: str) -> str:
    """データを分析して洞察を提供します。"""
    # 実際のアプリケーションではデータ分析ライブラリを使用します
    return f"「{data}」の分析結果: これはデータ分析のシミュレーションです。実際のアプリケーションではPandasなどを使用します。"

# 計画立案エージェント用のツール
@tool
def create_project_plan(project_description: str) -> str:
    """プロジェクトの計画を作成します。"""
    # 実際のアプリケーションではより複雑な計画立案ロジックを実装します
    steps = [
        "要件の分析と整理",
        "リソースの特定と割り当て",
        "タイムラインの作成",
        "リスク評価と対策の策定",
        "実行計画の確定"
    ]
    return f"「{project_description}」の計画:\n" + "\n".join([f"- {step}" for step in steps])

@tool
def estimate_resources(project_plan: str) -> str:
    """プロジェクト計画に基づいてリソース見積もりを行います。"""
    # 実際のアプリケーションではより複雑な見積もりロジックを実装します
    return f"「{project_plan}」のリソース見積もり: 人員: 3-5人、期間: 2-3週間、予算: 中規模"

# 実装エージェント用のツール
@tool
def generate_code(specification: str) -> str:
    """仕様に基づいてコードを生成します。"""
    # 実際のアプリケーションではより複雑なコード生成ロジックを実装します
    return f"""「{specification}」に基づくコード例:
```python
def main():
    print("仕様に基づいて実装されたコード")
    # ここに実際の実装が入ります
    
if __name__ == "__main__":
    main()
```"""

@tool
def test_code(code: str) -> str:
    """コードをテストして結果を返します。"""
    # 実際のアプリケーションでは実際にコードを実行してテストします
    return f"コードのテスト結果: テストは成功しました。カバレッジ: 85%"

# レビューエージェント用のツール
@tool
def review_solution(solution: str) -> str:
    """提案された解決策をレビューし、フィードバックを提供します。"""
    # 実際のアプリケーションではより詳細なレビュー基準を実装します
    return f"レビュー結果: 提案された解決策は概ね良好ですが、いくつかの改善点があります。"

# エージェントノードの作成
def create_research_agent():
    llm = ChatOpenAI(temperature=0.2)
    
    system_message = """あなたはリサーチエージェントです。
情報収集と分析が得意で、与えられたトピックについて徹底的に調査します。
他のエージェントと協力して、プロジェクトに必要な情報を提供してください。"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "{query}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_openai_tools_agent(llm, [search_information, analyze_data], prompt)
    
    agent_executor = AgentExecutor(
        agent=agent,
        tools=[search_information, analyze_data],
        verbose=True
    )
    
    return agent_executor

def create_planning_agent():
    llm = ChatOpenAI(temperature=0.2)
    
    system_message = """あなたは計画立案エージェントです。
プロジェクト管理とリソース配分が得意で、効率的な計画を立てます。
他のエージェントから提供された情報を基に、実行可能な計画を作成してください。"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "以下の情報に基づいて計画を立ててください:\nユーザーの要求: {query}\nリサーチ結果: {research_result}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_openai_tools_agent(llm, [create_project_plan, estimate_resources], prompt)
    
    agent_executor = AgentExecutor(
        agent=agent,
        tools=[create_project_plan, estimate_resources],
        verbose=True
    )
    
    return agent_executor

def create_implementation_agent():
    llm = ChatOpenAI(temperature=0.2)
    
    system_message = """あなたは実装エージェントです。
コーディングと技術的な実装が得意で、計画を実際のコードに変換します。
他のエージェントの計画に基づいて、高品質なコードを生成してください。"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "以下の計画に基づいてコードを生成してください:\nユーザーの要求: {query}\n計画: {planning_result}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_openai_tools_agent(llm, [generate_code, test_code], prompt)
    
    agent_executor = AgentExecutor(
        agent=agent,
        tools=[generate_code, test_code],
        verbose=True
    )
    
    return agent_executor

def create_review_agent():
    llm = ChatOpenAI(temperature=0.2)
    
    system_message = """あなたはレビューエージェントです。
提案された解決策を評価し、改善点を特定することが得意です。
実装結果を詳細にレビューし、改善が必要かどうかを判断してください。"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "以下の実装結果をレビューしてください:\nユーザーの要求: {query}\n実装結果: {implementation_result}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_openai_tools_agent(llm, [review_solution], prompt)
    
    agent_executor = AgentExecutor(
        agent=agent,
        tools=[review_solution],
        verbose=True
    )
    
    return agent_executor

# ノード関数の定義
async def research_node(state: AgentState) -> AgentState:
    """リサーチを行うノード"""
    global current_client_id
    
    if current_client_id:
        await manager.send_message(
            current_client_id,
            "リサーチエージェントが作業を開始します...",
            "research"
        )
    
    research_agent = create_research_agent()
    result = research_agent.invoke({"query": state["query"]})
    research_result = result["output"]
    
    if current_client_id:
        await manager.send_message(
            current_client_id,
            research_result,
            "research"
        )
    
    return {"query": state["query"], "research_result": research_result, "current_agent": "research"}

async def planning_node(state: AgentState) -> AgentState:
    """計画立案を行うノード"""
    global current_client_id
    
    if current_client_id:
        await manager.send_message(
            current_client_id,
            "計画立案エージェントが作業を開始します...",
            "planner"
        )
    
    planning_agent = create_planning_agent()
    result = planning_agent.invoke({
        "query": state["query"],
        "research_result": state["research_result"]
    })
    planning_result = result["output"]
    
    if current_client_id:
        await manager.send_message(
            current_client_id,
            planning_result,
            "planner"
        )
    
    return {**state, "planning_result": planning_result, "current_agent": "planner"}

async def implementation_node(state: AgentState) -> AgentState:
    """実装を行うノード"""
    global current_client_id
    
    if current_client_id:
        await manager.send_message(
            current_client_id,
            "実装エージェントが作業を開始します...",
            "implementer"
        )
    
    implementation_agent = create_implementation_agent()
    result = implementation_agent.invoke({
        "query": state["query"],
        "planning_result": state["planning_result"]
    })
    implementation_result = result["output"]
    
    if current_client_id:
        await manager.send_message(
            current_client_id,
            implementation_result,
            "implementer"
        )
    
    return {**state, "implementation_result": implementation_result, "current_agent": "implementer"}

async def review_node(state: AgentState) -> AgentState:
    """レビューを行うノード"""
    global current_client_id
    
    if current_client_id:
        await manager.send_message(
            current_client_id,
            "レビューエージェントが作業を開始します...",
            "reviewer"
        )
    
    review_agent = create_review_agent()
    result = review_agent.invoke({
        "query": state["query"],
        "implementation_result": state["implementation_result"]
    })
    feedback = result["output"]
    
    # レビュー結果に基づいて改善が必要かどうかを判断
    needs_revision = "改善" in feedback or "修正" in feedback
    
    if current_client_id:
        await manager.send_message(
            current_client_id,
            feedback,
            "reviewer"
        )
    
    return {**state, "feedback": feedback, "needs_revision": needs_revision, "current_agent": "reviewer"}

async def finalize_node(state: AgentState) -> AgentState:
    """最終結果をまとめるノード"""
    global current_client_id
    
    final_result = f"""
# 最終結果

## リサーチ結果
{state["research_result"]}

## 計画
{state["planning_result"]}

## 実装
{state["implementation_result"]}

## レビュー
{state["feedback"]}
"""
    
    if current_client_id:
        await manager.send_message(
            current_client_id,
            "最終結果をまとめています...",
            "system"
        )
        await manager.send_message(
            current_client_id,
            final_result,
            "system"
        )
    
    return {**state, "final_result": final_result, "current_agent": "finalized"}

# エッジの条件関数
def should_revise(state: AgentState) -> str:
    """レビュー結果に基づいて改善が必要かどうかを判断"""
    return "planning" if state.get("needs_revision", False) else "finalize"

# グラフの構築
async def build_graph():
    # 状態グラフの作成
    workflow = StateGraph(AgentState)
    
    # ノードの追加
    workflow.add_node("research", research_node)
    workflow.add_node("planning", planning_node)
    workflow.add_node("implementation", implementation_node)
    workflow.add_node("review", review_node)
    workflow.add_node("finalize", finalize_node)
    
    # エッジの追加（基本的な流れ）
    workflow.add_edge("research", "planning")
    workflow.add_edge("planning", "implementation")
    workflow.add_edge("implementation", "review")
    
    # 条件分岐: レビュー後に改善が必要なら計画に戻る、そうでなければ完了
    workflow.add_conditional_edges(
        "review",
        should_revise,
        {
            "planning": "planning",  # 改善が必要なら計画立案に戻る
            "finalize": "finalize"   # 問題なければ最終化
        }
    )
    
    # 最終ノードからの終了
    workflow.add_edge("finalize", END)
    
    # グラフのコンパイル
    return workflow.compile()

# グラフの実行関数
async def run_graph(query: str, client_id: str):
    global current_client_id
    current_client_id = client_id
    
    # グラフの構築
    graph = await build_graph()
    
    # メモリセーバーの設定
    memory = MemorySaver()
    
    # 初期状態の設定
    initial_state = {
        "query": query,
        "research_result": "",
        "planning_result": "",
        "implementation_result": "",
        "feedback": "",
        "final_result": "",
        "current_agent": "",
        "needs_revision": False
    }
    
    # グラフの実行
    for event in graph.stream(initial_state, config={"configurable": {"thread_id": client_id}}):
        # 状態の更新をログに出力
        print(f"Event: {event}")
    
    # 最終結果を取得
    thread_id = client_id
    events = memory.get_events(thread_id)
    final_state = events[-1].state
    
    return final_state

# APIエンドポイント
@app.get("/")
def read_root():
    return {"message": "LangGraph マルチエージェントオーケストレーションアプリへようこそ！"}

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    final_result: str

@app.post("/orchestrate", response_model=QueryResponse)
async def orchestrate_agents(request: QueryRequest):
    try:
        client_id = str(uuid.uuid4())
        final_state = await run_graph(request.query, client_id)
        
        return {
            "final_result": final_state["final_result"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"エラーが発生しました: {str(e)}")

# WebSocketエンドポイント
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            data_json = json.loads(data)
            query = data_json.get("query", "")
            
            if query:
                # 非同期でグラフを実行
                asyncio.create_task(run_graph(query, client_id))
    except WebSocketDisconnect:
        manager.disconnect(client_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
