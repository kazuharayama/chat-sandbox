from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
import tempfile
import shutil
from typing import List, Dict, Any, Optional
import uuid

# LangChain imports
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma, FAISS
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    CSVLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Langfuse import
from langfuse.langchain import CallbackHandler

# 環境変数の読み込み
load_dotenv()

# APIキーの確認
if not os.getenv("OPENAI_API_KEY"):
    print("警告: OPENAI_API_KEYが設定されていません。.envファイルに設定してください。")

# Langfuse設定の確認
if not os.getenv("LANGFUSE_HOST"):
    os.environ["LANGFUSE_HOST"] = "http://localhost:3000"
    print(f"LANGFUSE_HOST設定: {os.getenv('LANGFUSE_HOST')}")

# Langfuseハンドラーの初期化
try:
    langfuse_handler = CallbackHandler()
    print("Langfuseハンドラーが正常に初期化されました")
except Exception as e:
    print(f"Langfuseハンドラーの初期化に失敗しました: {e}")
    print("Langfuseトレーシングは無効になります。アプリケーションは正常に動作します。")
    langfuse_handler = None

# データ保存用ディレクトリの作成
DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
VECTOR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vectorstore")

os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(VECTOR_DIR, exist_ok=True)

# グローバル変数としてベクトルストアを保持
vector_store = None

# FastAPIアプリケーションの設定
app = FastAPI(title="LangChain RAGシステム")

# CORS設定を追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では特定のオリジンのみを許可するように変更すべき
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# モデルの定義
class DocumentRequest(BaseModel):
    document_type: str = Field(..., description="ドキュメントタイプ (pdf, text, markdown, csv)")

class QueryRequest(BaseModel):
    query: str
    language: str = "日本語"
    use_rag: bool = True

class ChatRequest(BaseModel):
    message: str
    language: str = "日本語"
    hasAttachment: bool = False
    use_rag: bool = True
    
class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []

class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    status: str

# ベクトルストアの初期化関数
def initialize_vector_store():
    global vector_store
    
    # すでにベクトルストアが存在する場合はロード
    if os.path.exists(VECTOR_DIR) and len(os.listdir(VECTOR_DIR)) > 0:
        try:
            embeddings = OpenAIEmbeddings()
            vector_store = FAISS.load_local(VECTOR_DIR, embeddings)
            print("Existing vector store loaded successfully")
            return vector_store
        except Exception as e:
            print(f"Error loading vector store: {e}")
    
    # ドキュメントがあれば新しくベクトルストアを作成
    if os.path.exists(DOCS_DIR) and len(os.listdir(DOCS_DIR)) > 0:
        try:
            documents = []
            for filename in os.listdir(DOCS_DIR):
                file_path = os.path.join(DOCS_DIR, filename)
                if filename.endswith(".pdf"):
                    loader = PyPDFLoader(file_path)
                    documents.extend(loader.load())
                elif filename.endswith(".txt"):
                    loader = TextLoader(file_path)
                    documents.extend(loader.load())
                elif filename.endswith(".md"):
                    loader = UnstructuredMarkdownLoader(file_path)
                    documents.extend(loader.load())
                elif filename.endswith(".csv"):
                    loader = CSVLoader(file_path)
                    documents.extend(loader.load())
            
            if documents:
                # テキスト分割
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200
                )
                chunks = text_splitter.split_documents(documents)
                
                # ベクトルストアの作成
                embeddings = OpenAIEmbeddings()
                vector_store = FAISS.from_documents(chunks, embeddings)
                
                # ベクトルストアの保存
                vector_store.save_local(VECTOR_DIR)
                print("New vector store created and saved successfully")
                return vector_store
        except Exception as e:
            print(f"Error creating vector store: {e}")
    
    return None

# アプリ起動時にベクトルストアを初期化
@app.on_event("startup")
async def startup_event():
    initialize_vector_store()

@app.get("/")
def read_root():
    return {"message": "LangChain RAGシステムへようこそ！"}

@app.post("/upload", response_model=DocumentResponse)
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...), document_type: str = Form(...)):
    try:
        # ファイル拡張子の確認
        valid_extensions = {
            "pdf": ".pdf",
            "text": ".txt",
            "markdown": ".md",
            "csv": ".csv"
        }
        
        if document_type not in valid_extensions:
            raise HTTPException(status_code=400, detail=f"サポートされていないドキュメントタイプです: {document_type}")
        
        # ファイル名の生成
        document_id = str(uuid.uuid4())
        original_filename = file.filename
        extension = valid_extensions[document_type]
        filename = f"{document_id}{extension}"
        file_path = os.path.join(DOCS_DIR, filename)
        
        # ファイルの保存
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # バックグラウンドタスクでベクトルストアを更新
        background_tasks.add_task(initialize_vector_store)
        
        return {
            "document_id": document_id,
            "filename": original_filename,
            "status": "アップロード成功、インデックス作成中"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ドキュメントアップロード中にエラーが発生しました: {str(e)}")

@app.get("/documents")
async def list_documents():
    try:
        documents = []
        if os.path.exists(DOCS_DIR):
            for filename in os.listdir(DOCS_DIR):
                file_path = os.path.join(DOCS_DIR, filename)
                if os.path.isfile(file_path):
                    document_id = os.path.splitext(filename)[0]
                    documents.append({
                        "document_id": document_id,
                        "filename": filename,
                        "size": os.path.getsize(file_path),
                        "last_modified": os.path.getmtime(file_path)
                    })
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ドキュメント一覧取得中にエラーが発生しました: {str(e)}")

@app.post("/query", response_model=ChatResponse)
async def query_documents(request: QueryRequest):
    try:
        global vector_store
        
        if request.use_rag and vector_store is None:
            # ベクトルストアがない場合は初期化を試みる
            vector_store = initialize_vector_store()
        
        # LLMの初期化
        llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL_NAME", "gpt-4"),
            temperature=0.7
        )
        
        if request.use_rag and vector_store:
            # RAGを使用した質問応答
            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}
            )
            
            # プロンプトテンプレート
            template = """次の質問に{language}で答えてください。与えられたドキュメントの情報を使用して回答してください。ドキュメントに情報がない場合は、その旨を正直に伝えてください。

質問: {question}

ドキュメント:
{context}
"""
            prompt = ChatPromptTemplate.from_template(template)
            
            # RAGチェーンの構築
            rag_chain = (
                {"context": retriever, "question": RunnablePassthrough(), "language": lambda _: request.language}
                | prompt
                | llm
                | StrOutputParser()
            )
            
            # ドキュメント取得と結果の生成
            docs = retriever.get_relevant_documents(request.query)
            sources = [doc.metadata.get("source", "不明なソース") for doc in docs]
            
            # Langfuseトレースを含めてRAGチェーンを実行
            config = {"callbacks": [langfuse_handler]} if langfuse_handler else {}
            response = rag_chain.invoke(request.query, config=config)
            
            return {"response": response, "sources": sources}
        else:
            # 通常の質問応答
            prompt = ChatPromptTemplate.from_template(
                "次の質問に{language}で答えてください: {query}"
            )
            chain = prompt | llm | StrOutputParser()
            
            # Langfuseトレースを含めて通常のチェーンを実行
            config = {"callbacks": [langfuse_handler]} if langfuse_handler else {}
            response = chain.invoke({"query": request.query, "language": request.language}, config=config)
            
            return {"response": response, "sources": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"クエリ処理中にエラーが発生しました: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        global vector_store
        
        if request.use_rag and vector_store is None:
            # ベクトルストアがない場合は初期化を試みる
            vector_store = initialize_vector_store()
        
        # LLMの初期化
        llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL_NAME", "gpt-4"),
            temperature=0.7
        )
        
        # 入力メッセージの処理
        input_text = request.message
        has_attachment = request.hasAttachment
        
        if request.use_rag and vector_store:
            # RAGを使用したチャット応答
            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}
            )
            
            # プロンプトテンプレート
            if has_attachment:
                template = """ユーザーが画像を添付して次のメッセージを送信しました: {message}

画像の内容については分かりませんが、画像が添付されていることを考慮して、{language}で適切に返答してください。
以下の関連ドキュメントの情報も参考にしてください。ドキュメントに関連情報がない場合は無視してください。
返答は会話的で親しみやすい口調にしてください。

関連ドキュメント:
{context}"""
            else:
                template = """ユーザーからの次のメッセージに対して、{language}で適切に返答してください: {message}

以下の関連ドキュメントの情報も参考にしてください。ドキュメントに関連情報がない場合は無視してください。
返答は会話的で親しみやすい口調にしてください。

関連ドキュメント:
{context}"""
            
            prompt = ChatPromptTemplate.from_template(template)
            
            # RAGチェーンの構築
            rag_chain = (
                {"context": retriever, "message": RunnablePassthrough(), "language": lambda _: request.language}
                | prompt
                | llm
                | StrOutputParser()
            )
            
            # ドキュメント取得と結果の生成
            docs = retriever.get_relevant_documents(input_text)
            sources = [doc.metadata.get("source", "不明なソース") for doc in docs]
            
            # Langfuseトレースを含めてRAGチェーンを実行
            try:
                config = {"callbacks": [langfuse_handler]} if langfuse_handler else {}
                response = rag_chain.invoke(input_text, config=config)
            except Exception as callback_error:
                print(f"Langfuseコールバックエラーを無視して実行を継続: {callback_error}")
                response = rag_chain.invoke(input_text)
            
            return {"response": response, "sources": sources}
        else:
            # 通常のチャット応答
            if has_attachment:
                prompt_template = """ユーザーが画像を添付して次のメッセージを送信しました: {message}

画像の内容については分かりませんが、画像が添付されていることを考慮して、{language}で適切に返答してください。
返答は会話的で親しみやすい口調にしてください。"""
            else:
                prompt_template = """ユーザーからの次のメッセージに対して、{language}で適切に返答してください: {message}

返答は会話的で親しみやすい口調にしてください。"""
            
            prompt = ChatPromptTemplate.from_template(prompt_template)
            chain = prompt | llm | StrOutputParser()
            
            # Langfuseトレースを含めて通常のチェーンを実行
            config = {"callbacks": [langfuse_handler]} if langfuse_handler else {}
            response = chain.invoke({"message": input_text, "language": request.language}, config=config)
            
            return {"response": response, "sources": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"チャット処理中にエラーが発生しました: {str(e)}")

@app.post("/speech-to-text")
async def speech_to_text(audio: UploadFile = File(...)):
    try:
        # 実際の実装では、ここで音声ファイルを処理して
        # 音声認識APIを使用してテキストに変換します
        # 例: Whisper APIなど
        
        # このサンプルでは、単にダミーレスポンスを返します
        return {"text": "音声認識されたテキストがここに表示されます"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"音声認識中にエラーが発生しました: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
