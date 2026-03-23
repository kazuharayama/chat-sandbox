import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# Azure OpenAI設定の確認
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
AZURE_OPENAI_LLM_DEPLOYMENT = os.getenv("AZURE_OPENAI_LLM_DEPLOYMENT", "gpt-4o")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")

if not AZURE_OPENAI_API_KEY:
    print("警告: AZURE_OPENAI_API_KEYが設定されていません。.envファイルに設定してください。")
if not AZURE_OPENAI_ENDPOINT:
    print("警告: AZURE_OPENAI_ENDPOINTが設定されていません。.envファイルに設定してください。")

# データ保存用ディレクトリの設定
DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")

os.makedirs(DOCS_DIR, exist_ok=True)
