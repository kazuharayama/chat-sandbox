#!/bin/bash

# 色の定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}LangGraph マルチエージェントオーケストレーションアプリを起動します...${NC}"

# 仮想環境の確認と作成
if [ ! -d "venv" ]; then
    echo -e "${BLUE}Python仮想環境を作成しています...${NC}"
    python -m venv venv
fi

# 仮想環境のアクティベート
source venv/bin/activate

# バックエンド依存関係のインストール
echo -e "${BLUE}バックエンドの依存関係をインストールしています...${NC}"
pip install -r backend/requirements.txt

# フロントエンドの依存関係の確認とインストール
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${BLUE}フロントエンドの依存関係をインストールしています...${NC}"
    cd frontend && npm install && cd ..
fi

# バックエンドとフロントエンドを起動
echo -e "${GREEN}バックエンドサーバーを起動しています...${NC}"
cd backend
python langgraph_multi_agent.py &
BACKEND_PID=$!
cd ..

echo -e "${GREEN}フロントエンドサーバーを起動しています...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo -e "${GREEN}アプリケーションが起動しました！${NC}"
echo -e "${BLUE}バックエンド: http://localhost:8000${NC}"
echo -e "${BLUE}フロントエンド: http://localhost:5173${NC}"
echo -e "${RED}終了するには Ctrl+C を押してください${NC}"

# 終了時に両方のプロセスを終了
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
