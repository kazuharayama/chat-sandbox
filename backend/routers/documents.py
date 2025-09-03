from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List
import os
import uuid
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    CSVLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from config import DOCS_DIR, VECTOR_DIR, get_vector_store, set_vector_store

router = APIRouter()

class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    status: str

def initialize_vector_store():
    """ベクトルストアの初期化関数"""
    current_vector_store = get_vector_store()
    
    # すでにベクトルストアが存在する場合はロード
    if os.path.exists(VECTOR_DIR) and len(os.listdir(VECTOR_DIR)) > 0:
        try:
            embeddings = OpenAIEmbeddings()
            vector_store = FAISS.load_local(VECTOR_DIR, embeddings)
            set_vector_store(vector_store)
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
                set_vector_store(vector_store)
                print("New vector store created and saved successfully")
                return vector_store
        except Exception as e:
            print(f"Error creating vector store: {e}")
    
    return None

@router.post("/upload", response_model=DocumentResponse)
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

@router.get("/documents")
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
