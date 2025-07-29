# ベースイメージとして共通の依存関係をインストール
FROM python:3.11-slim AS base

WORKDIR /app

# 依存関係ファイルをコピー
COPY requirements.txt .

# 共通の依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# 開発環境用ステージ
FROM base AS development

# 開発用ツールをインストール
RUN pip install --no-cache-dir pytest pytest-cov debugpy

# アプリケーションコードをコピー
COPY . .

# ポートを公開
EXPOSE 8000 5678

# デバッグモードで実行可能なコマンド
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# 本番環境用ステージ
FROM base AS production

# 非rootuserを作成
RUN groupadd -r appuser && useradd -r -g appuser appuser

# アプリケーションコードをコピー
COPY . .

# 権限設定
RUN chown -R appuser:appuser /app
USER appuser

# ポートを公開
EXPOSE 8000

# 本番環境用の起動コマンド
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
