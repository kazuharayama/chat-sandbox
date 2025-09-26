import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# APIキーの確認
if not os.getenv("OPENAI_API_KEY"):
    print("警告: OPENAI_API_KEYが設定されていません。.envファイルに設定してください。")

# データ保存用ディレクトリの設定
DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")

os.makedirs(DOCS_DIR, exist_ok=True)
