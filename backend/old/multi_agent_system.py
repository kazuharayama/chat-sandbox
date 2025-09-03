from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.pydantic_v1 import BaseModel, Field
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel as PydanticBaseModel
import json
import asyncio
import uuid
from dotenv import load_dotenv
import os

# 環境変数の読み込み
load_dotenv()

# APIキーの確認
if not os.getenv("OPENAI_API_KEY"):
    print("警告: OPENAI_API_KEYが設定されていません。.envファイルに設定してください。")

app = FastAPI(title="LangChain マルチエージェントオーケストレーションアプリ")

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

# エージェントの作成関数
def create_agent(role: str, tools_list):
    llm = ChatOpenAI(temperature=0.2)
    
    if role == "research":
        system_message = """あなたはリサーチエージェントです。
情報収集と分析が得意で、与えられたトピックについて徹底的に調査します。
他のエージェントと協力して、プロジェクトに必要な情報を提供してください。"""
    elif role == "planner":
        system_message = """あなたは計画立案エージェントです。
プロジェクト管理とリソース配分が得意で、効率的な計画を立てます。
他のエージェントから提供された情報を基に、実行可能な計画を作成してください。"""
    elif role == "implementer":
        system_message = """あなたは実装エージェントです。
コーディングと技術的な実装が得意で、計画を実際のコードに変換します。
他のエージェントの計画に基づいて、高品質なコードを生成してください。"""
    else:
        system_message = "あなたは汎用AIアシスタントです。"
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    
    agent = create_openai_tools_agent(llm, tools_list, prompt)
    
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools_list,
        memory=memory,
        verbose=True
    )
    
    return agent_executor

# エージェントの初期化
research_agent = create_agent("research", [search_information, analyze_data])
planner_agent = create_agent("planner", [create_project_plan, estimate_resources])
implementer_agent = create_agent("implementer", [generate_code, test_code])

# マルチエージェントオーケストレーションクラス
class MultiAgentOrchestrator:
    def __init__(self):
        self.agents = {
            "research": research_agent,
            "planner": planner_agent,
            "implementer": implementer_agent
        }
        self.conversation_history = []
    
    async def process_query(self, query: str, client_id: str):
        # 最初のメッセージをユーザーからのものとして追加
        self.conversation_history.append({"role": "user", "content": query})
        
        # 1. リサーチエージェントに情報収集を依頼
        research_prompt = f"次のトピックについて情報を収集してください: {query}"
        research_result = await self.run_agent("research", research_prompt, client_id)
        
        # 2. 計画立案エージェントに計画作成を依頼
        planning_prompt = f"以下の情報に基づいて計画を立ててください:\nユーザーの要求: {query}\nリサーチ結果: {research_result}"
        planning_result = await self.run_agent("planner", planning_prompt, client_id)
        
        # 3. 実装エージェントにコード生成を依頼
        implementation_prompt = f"以下の計画に基づいてコードを生成してください:\nユーザーの要求: {query}\n計画: {planning_result}"
        implementation_result = await self.run_agent("implementer", implementation_prompt, client_id)
        
        # 最終結果をまとめる
        final_result = {
            "research": research_result,
            "planning": planning_result,
            "implementation": implementation_result
        }
        
        return final_result
    
    async def run_agent(self, agent_type: str, prompt: str, client_id: str):
        # エージェントからのメッセージをクライアントに送信
        await manager.send_message(
            client_id,
            f"エージェント「{agent_type}」が作業を開始します...",
            agent_type
        )
        
        # エージェントを実行
        result = self.agents[agent_type].invoke({"input": prompt})
        output = result.get("output", "結果がありません")
        
        # エージェントの結果をクライアントに送信
        await manager.send_message(client_id, output, agent_type)
        
        # 会話履歴に追加
        self.conversation_history.append({"role": agent_type, "content": output})
        
        return output

# オーケストレーターのインスタンスを作成
orchestrator = MultiAgentOrchestrator()

# APIエンドポイント
@app.get("/")
def read_root():
    return {"message": "LangChain マルチエージェントオーケストレーションアプリへようこそ！"}

class QueryRequest(PydanticBaseModel):
    query: str

class QueryResponse(PydanticBaseModel):
    research_result: str
    planning_result: str
    implementation_result: str

@app.post("/orchestrate", response_model=QueryResponse)
async def orchestrate_agents(request: QueryRequest):
    try:
        client_id = str(uuid.uuid4())
        result = await orchestrator.process_query(request.query, client_id)
        
        return {
            "research_result": result["research"],
            "planning_result": result["planning"],
            "implementation_result": result["implementation"]
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
                # 非同期でオーケストレーションを実行
                asyncio.create_task(orchestrator.process_query(query, client_id))
    except WebSocketDisconnect:
        manager.disconnect(client_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
