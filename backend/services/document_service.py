import logging
import os
import uuid
from typing import List, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    CSVLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)

from models.document import DocumentInfo, DocumentUploadResponse
from repositories.document_repository import DocumentRepository
from repositories.image_repository import ImageRepository
from repositories.vector_repository import VectorRepository

logger = logging.getLogger(__name__)

VALID_EXTENSIONS = {
    "pdf": ".pdf",
    "text": ".txt",
    "markdown": ".md",
    "csv": ".csv",
    "image": None,
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}

LOADERS = {
    ".pdf": PyPDFLoader,
    ".txt": TextLoader,
    ".md": UnstructuredMarkdownLoader,
    ".csv": CSVLoader,
}


class DocumentService:
    def __init__(
        self,
        document_repo: DocumentRepository,
        vector_repo: Optional[VectorRepository],
        image_repo: Optional[ImageRepository] = None,
    ):
        self.document_repo = document_repo
        self.vector_repo = vector_repo
        self.image_repo = image_repo
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )

    async def upload_document(
        self, content: bytes, original_filename: str, document_type: str
    ) -> DocumentUploadResponse:
        if document_type not in VALID_EXTENSIONS:
            raise ValueError(f"サポートされていないドキュメントタイプです: {document_type}")

        document_id = str(uuid.uuid4())

        if document_type == "image":
            extension = os.path.splitext(original_filename)[1].lower()
            if extension not in IMAGE_EXTENSIONS:
                raise ValueError(f"サポートされていない画像形式です: {extension}")
        else:
            extension = VALID_EXTENSIONS[document_type]

        filename = f"{document_id}{extension}"

        file_path = await self.document_repo.save_file(content, filename)
        logger.info("Document uploaded: %s (%s)", original_filename, document_id)

        return DocumentUploadResponse(
            document_id=document_id,
            filename=original_filename,
            status="アップロード成功、インデックス作成中",
        ), file_path, document_id

    def process_document(self, file_path: str, document_id: str) -> None:
        extension = "." + file_path.rsplit(".", 1)[-1].lower()

        # 画像 → CLIP でベクトル化
        if extension in IMAGE_EXTENSIONS:
            if not self.image_repo:
                logger.warning("ImageRepository not available, skipping image indexing")
                return
            self.image_repo.add_image(file_path, document_id)
            logger.info("Image %s indexed with CLIP", document_id)
            return

        # テキスト文書 → Azure OpenAI Embedding でベクトル化
        if not self.vector_repo:
            logger.warning("VectorRepository not available, skipping indexing")
            return

        loader_cls = LOADERS.get(extension)
        if not loader_cls:
            logger.warning("No loader for extension: %s", extension)
            return

        loader = loader_cls(file_path)
        documents = loader.load()
        for doc in documents:
            doc.metadata["document_id"] = document_id
            doc.metadata["source"] = file_path

        chunks = self.text_splitter.split_documents(documents)
        self.vector_repo.add_documents(chunks)
        logger.info("Document %s processed and indexed (%d chunks)", document_id, len(chunks))

    def list_documents(self) -> List[DocumentInfo]:
        return self.document_repo.list_documents()
