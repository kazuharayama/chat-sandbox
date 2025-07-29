#!/bin/bash

# Azure環境へのデプロイスクリプト
cd "$(dirname "$0")/.."
echo "Azure環境にデプロイします..."

# 引数チェック
ENVIRONMENT=${1:-dev}
if [ "$ENVIRONMENT" != "dev" ] && [ "$ENVIRONMENT" != "prod" ]; then
  echo "環境は 'dev' または 'prod' を指定してください"
  echo "使用方法: $0 [dev|prod]"
  exit 1
fi

# 環境変数ファイルが存在する場合は読み込む
ENV_FILE=".env.azure.$ENVIRONMENT"
if [ -f "$ENV_FILE" ]; then
  export $(grep -v '^#' "$ENV_FILE" | xargs)
else
  echo "警告: $ENV_FILE が見つかりません。必要な環境変数が設定されていることを確認してください。"
fi

# 必須環境変数のチェック
REQUIRED_VARS=("AZURE_CONTAINER_REGISTRY" "APP_NAME" "IMAGE_TAG")
for VAR in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!VAR}" ]; then
    echo "エラー: 環境変数 $VAR が設定されていません"
    exit 1
  fi
done

# Azure CLIでログインしているか確認
az account show &> /dev/null
if [ $? -ne 0 ]; then
  echo "Azure CLIにログインしていません。ログインしてください..."
  az login
fi

# Azure Container Registryにログイン
echo "Azure Container Registryにログイン: $AZURE_CONTAINER_REGISTRY"
az acr login --name $AZURE_CONTAINER_REGISTRY

# イメージのビルドとプッシュ
echo "Dockerイメージをビルドしてプッシュします..."
docker-compose -f docker-compose.azure.yml build
docker-compose -f docker-compose.azure.yml push

# Terraformでインフラをデプロイ
echo "Terraformでインフラをデプロイします..."
cd ../../terraform/environments/$ENVIRONMENT

# Terraformの初期化と適用
terraform init
terraform plan -out=tfplan
terraform apply -auto-approve tfplan

# デプロイ完了後の情報表示
APP_URL=$(terraform output -raw app_url)
echo "Azure環境へのデプロイが完了しました"
echo "アプリケーションは $APP_URL で利用可能です"
