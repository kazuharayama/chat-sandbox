# ベースイメージとして共通の依存関係をインストール
FROM node:20-alpine AS base

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm ci

# 開発環境用ステージ
FROM base AS development

# Copy the rest of the application code
COPY . .

# Expose the development port
EXPOSE 5174

# 開発環境用の起動コマンド
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# 本番環境用ステージ
FROM base AS production

# Copy the rest of the application code
COPY . .

# Build the application for production
RUN npm run build

# Expose the production port
EXPOSE 4173

# 本番環境用の起動コマンド
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0"]
