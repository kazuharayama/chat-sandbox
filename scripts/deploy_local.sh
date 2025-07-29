#!/bin/bash

# ローカル環境へのデプロイスクリプト
cd "$(dirname "$0")/.."
echo "ローカル環境にデプロイします..."

# 環境変数ファイルが存在する場合は読み込む
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# ローカル環境用のdocker-composeを実行
docker-compose down
docker-compose build
docker-compose up -d

echo "ローカル環境へのデプロイが完了しました"
echo "アプリケーションは http://localhost で利用可能です"
