from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.agents import AgentExecutor, create_openai_tools_agent
from typing import Dict, List, Any, TypedDict, Annotated, Sequence, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import json
import asyncio
import uuid
from dotenv import load_dotenv
import os
import datetime

# LangGraphのインポート
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

# 環境変数の読み込み
load_dotenv()

# APIキーの確認
if not os.getenv("OPENAI_API_KEY"):
    print("警告: OPENAI_API_KEYが設定されていません。.envファイルに設定してください。")

app = FastAPI(title="Root Cause Analysis (RCA) システム")

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
class RCAState(TypedDict):
    problem_description: str
    symptoms: List[str]
    data_points: List[Dict[str, Any]]
    potential_causes: List[Dict[str, Any]]
    root_causes: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    current_step: str
    analysis_complete: bool
    feedback: Optional[str]

# 問題定義エージェント用のツール
@tool
def define_problem(description: str) -> str:
    """問題の詳細な定義と範囲を明確にします。"""
    return f"問題定義: {description}\n\n問題の範囲と影響が明確になりました。"

@tool
def identify_symptoms(problem: str) -> str:
    """問題の主な症状を特定します。"""
    # 実際のアプリケーションではより詳細な分析を行います
    return f"「{problem}」の主な症状:\n- パフォーマンスの低下\n- エラーの発生\n- 予期しない動作"

# データ収集エージェント用のツール
@tool
def collect_logs(system_name: str, time_period: str) -> str:
    """指定されたシステムのログを収集します。"""
    # 実際のアプリケーションでは実際のログ収集を行います
    return f"{system_name}の{time_period}のログを収集しました。エラーパターンがいくつか見つかりました。"

@tool
def gather_metrics(metric_name: str, time_period: str) -> str:
    """指定されたメトリクスのデータを収集します。"""
    # 実際のアプリケーションでは実際のメトリクス収集を行います
    return f"{metric_name}の{time_period}のメトリクスを収集しました。通常より30%高い値が観測されています。"

@tool
def interview_stakeholders(question: str) -> str:
    """ステークホルダーへの質問結果をシミュレートします。"""
    responses = {
        "いつから問題が発生していますか？": "先週の火曜日のシステムアップデート後から問題が発生しています。",
        "どのような状況で問題が発生しますか？": "主に高負荷時（ユーザー数が1000人を超える時）に問題が発生します。",
        "以前にも同様の問題はありましたか？": "3ヶ月前に一度似たような問題がありましたが、その時はサーバー再起動で解決しました。",
        "最近システムに変更はありましたか？": "先週のアップデートでデータベースの設定を変更しました。",
    }
    
    for key in responses:
        if key in question:
            return responses[key]
    
    return "その質問に対する具体的な情報はありません。もう少し具体的な質問をしてください。"

# 分析エージェント用のツール
@tool
def analyze_timeline(events: str) -> str:
    """イベントのタイムラインを分析して相関関係を見つけます。"""
    # 実際のアプリケーションではより詳細なタイムライン分析を行います
    return "タイムライン分析の結果、問題はシステムアップデート直後に発生し始めたことが確認されました。"

@tool
def perform_five_whys(initial_problem: str) -> str:
    """5回「なぜ」を繰り返して根本原因を探ります。"""
    whys = [
        f"なぜ{initial_problem}が発生したのか？ → システムの応答時間が遅延しているため",
        "なぜシステムの応答時間が遅延しているのか？ → データベースクエリの実行に時間がかかっているため",
        "なぜデータベースクエリの実行に時間がかかるのか？ → インデックスが最適化されていないため",
        "なぜインデックスが最適化されていないのか？ → 最近のスキーマ変更後にインデックスが更新されていないため",
        "なぜスキーマ変更後にインデックスが更新されていないのか？ → デプロイメントプロセスにインデックス更新の手順が含まれていないため"
    ]
    return "\n".join(whys)

@tool
def check_similar_incidents(problem_type: str) -> str:
    """類似のインシデント履歴を確認します。"""
    # 実際のアプリケーションでは過去のインシデントデータベースを検索します
    return f"{problem_type}に関連する過去のインシデント: 3件見つかりました。すべて同様のデータベース設定の問題が原因でした。"

# 根本原因特定エージェント用のツール
@tool
def identify_root_causes(analysis_data: str) -> str:
    """分析データから根本原因を特定します。"""
    # 実際のアプリケーションではより複雑な分析を行います
    return """特定された根本原因:
1. プライマリ: デプロイメントプロセスの不備（インデックス更新ステップの欠如）
2. セカンダリ: 変更管理プロセスの不備（変更の影響評価が不十分）
3. コントリビューティング: パフォーマンステストの不足（本番環境に類似した負荷テストが行われていない）"""

@tool
def validate_root_cause(cause: str, evidence: str) -> str:
    """提案された根本原因が正しいかを検証します。"""
    # 実際のアプリケーションではより詳細な検証を行います
    return f"根本原因「{cause}」の検証結果: 収集された証拠と一致しています。この原因が問題を説明できます。"

# 推奨事項作成エージェント用のツール
@tool
def generate_recommendations(root_causes: str) -> str:
    """特定された根本原因に基づいて推奨事項を生成します。"""
    return """推奨事項:
1. 短期対策: データベースインデックスの即時再構築
2. 中期対策: デプロイメントプロセスにインデックス更新ステップを追加
3. 長期対策: 変更管理プロセスの見直しと改善
4. 予防策: 本番環境に類似した負荷テストの定期的な実施"""

@tool
def prioritize_actions(recommendations: str) -> str:
    """推奨される対策に優先順位をつけます。"""
    return """優先順位付き対策:
1. 最高（即時対応）: データベースインデックスの再構築
2. 高（1週間以内）: デプロイメントプロセスの更新
3. 中（1ヶ月以内）: 変更管理プロセスの見直し
4. 継続的: 定期的な負荷テストの実施"""

# レポート生成エージェント用のツール
@tool
def generate_rca_report(state_data: str) -> str:
    """RCA分析の結果をレポート形式にまとめます。"""
    # 実際のアプリケーションではより詳細なレポートを生成します
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    return f"""# 根本原因分析（RCA）レポート
## 作成日: {today}

### 問題概要
{state_data}

### 分析手法
- 5 Whys分析
- タイムライン分析
- 類似インシデントの調査
- ステークホルダーインタビュー

### 特定された根本原因
1. プライマリ: デプロイメントプロセスの不備
2. セカンダリ: 変更管理プロセスの不備
3. コントリビューティング: パフォーマンステストの不足

### 推奨対策
1. 短期対策: データベースインデックスの即時再構築
2. 中期対策: デプロイメントプロセスの改善
3. 長期対策: 変更管理プロセスの見直し
4. 予防策: 定期的な負荷テストの実施

### フォローアップ
- 1週間後: 短期対策の効果確認
- 1ヶ月後: 中期対策の実施状況確認
- 3ヶ月後: 長期対策の進捗確認
"""
