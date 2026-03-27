from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile

from core.dependencies import get_document_service
from models.document import DocumentUploadResponse
from services.document_service import DocumentService

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    document_service: DocumentService = Depends(get_document_service),
):
    try:
        content = await file.read()
        response, file_path, document_id = await document_service.upload_document(
            content, file.filename, document_type
        )
        background_tasks.add_task(document_service.process_document, file_path, document_id)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ドキュメントアップロード中にエラーが発生しました: {str(e)}",
        )


@router.get("/documents")
async def list_documents(
    document_service: DocumentService = Depends(get_document_service),
):
    try:
        documents = document_service.list_documents()
        return {"documents": [doc.model_dump() for doc in documents]}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ドキュメント一覧取得中にエラーが発生しました: {str(e)}",
        )
