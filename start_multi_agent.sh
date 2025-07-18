#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}LangChain マルチエージェントオーケストレーションアプリ起動スクリプト${NC}"
echo "=================================================="

# バックエンドの起動
echo -e "${GREEN}バックエンドを起動しています...${NC}"
cd backend
echo "Python 仮想環境をセットアップ中..."
python -m venv venv
source venv/bin/activate
echo "依存関係をインストール中..."
pip install -r requirements.txt
echo "マルチエージェントバックエンドサーバーを起動中..."
uvicorn multi_agent_system:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# フロントエンドの起動
echo -e "${GREEN}フロントエンドを起動しています...${NC}"
cd frontend
echo "依存関係をインストール中..."
npm install
echo "開発サーバーを起動中..."
npm run dev &
FRONTEND_PID=$!
cd ..

echo -e "${GREEN}アプリケーションが起動しました！${NC}"
echo "バックエンド: http://localhost:8000"
echo "フロントエンド: http://localhost:5173"
echo ""
echo "Ctrl+C で両方のサーバーを停止します"

# 終了時に両方のプロセスを終了
function cleanup {
  echo -e "${BLUE}サーバーを停止しています...${NC}"
  kill $BACKEND_PID
  kill $FRONTEND_PID
  echo "終了しました。"
}

trap cleanup EXIT

# スクリプトが終了しないように待機
wait
