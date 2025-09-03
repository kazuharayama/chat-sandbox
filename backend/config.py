import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# 環境変数の読み込み
load_dotenv()

# APIキーの確認
if not os.getenv("OPENAI_API_KEY"):
    print("警告: OPENAI_API_KEYが設定されていません。.envファイルに設定してください。")

# データ保存用ディレクトリの設定
DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
VECTOR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vectorstore")

os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(VECTOR_DIR, exist_ok=True)

# グローバル変数としてベクトルストアを保持
vector_store = None

def get_vector_store():
    """ベクトルストアのゲッター"""
    global vector_store
    return vector_store

def set_vector_store(new_vector_store):
    """ベクトルストアのセッター"""
    global vector_store
    vector_store = new_vector_store
