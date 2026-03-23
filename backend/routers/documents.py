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
from langchain_openai import AzureOpenAIEmbeddings
from utils.pgvector_manager import PGVectorManager
from config import DOCS_DIR

router = APIRouter()

class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    status: str

def initialize_vector_store():
    """ベクトルストアの初期化関数"""
    try:
        # PGVectorManagerのインスタンスを取得
        vector_manager = PGVectorManager.get_instance()
        print("PGVector store initialized successfully")
        return vector_manager
    except Exception as e:
        print(f"Error initializing PGVector store: {e}") 
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
        background_tasks.add_task(process_document, file_path, document_id)
        
        return {
            "document_id": document_id,
            "filename": original_filename,
            "status": "アップロード成功、インデックス作成中"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ドキュメントアップロード中にエラーが発生しました: {str(e)}")

def process_document(file_path: str, document_id: str):
    """Process uploaded document and add to vector store."""
    try:
        documents = []
        
        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
            documents.extend(loader.load())
        elif file_path.endswith(".txt"):
            loader = TextLoader(file_path)
            documents.extend(loader.load())
        elif file_path.endswith(".md"):
            loader = UnstructuredMarkdownLoader(file_path)
            documents.extend(loader.load())
        elif file_path.endswith(".csv"):
            loader = CSVLoader(file_path)
            documents.extend(loader.load())
        
        if documents:
            # Add document metadata
            for doc in documents:
                doc.metadata["document_id"] = document_id
                doc.metadata["source"] = file_path
            
            # Text splitting
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            chunks = text_splitter.split_documents(documents)
            
            # Add to PGVector store
            vector_manager = PGVectorManager.get_instance()
            vector_manager.add_documents(chunks)
            
            print(f"Document {document_id} processed and added to vector store")
        
    except Exception as e:
        print(f"Error processing document {document_id}: {e}")

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
