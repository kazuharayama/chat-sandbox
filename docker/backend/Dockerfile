# ベースイメージとして共通の依存関係をインストール
FROM python:3.11-slim AS base

WORKDIR /app

# システム依存関係をインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-jpn \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 依存関係ファイルをコピー
COPY requirements.txt .

# 共通の依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# Piper TTS バイナリとモデルをダウンロード
RUN pip install --no-cache-dir piper-tts==1.2.0 && \
    mkdir -p /app/models/piper && \
    wget -q -O /app/models/piper/ja_JP-amitaro-medium.onnx \
      "https://huggingface.co/rhasspy/piper-voices/resolve/main/ja/ja_JP/amitaro/medium/ja_JP-amitaro-medium.onnx" && \
    wget -q -O /app/models/piper/ja_JP-amitaro-medium.onnx.json \
      "https://huggingface.co/rhasspy/piper-voices/resolve/main/ja/ja_JP/amitaro/medium/ja_JP-amitaro-medium.onnx.json"

# faster-whisper モデルをプリダウンロード
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"

# 開発環境用ステージ
FROM base AS development

# 開発用ツールをインストール
RUN pip install --no-cache-dir pytest pytest-cov debugpy

# アプリケーションコードをコピー
COPY . .

# ポートを公開
EXPOSE 8000 5678

# デバッグモードで実行可能なコマンド
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

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
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
