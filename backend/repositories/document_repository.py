import logging
import os
from typing import List

from models.document import DocumentInfo

logger = logging.getLogger(__name__)


class DocumentRepository:
    def __init__(self, docs_dir: str):
        self.docs_dir = docs_dir
        os.makedirs(self.docs_dir, exist_ok=True)

    async def save_file(self, content: bytes, filename: str) -> str:
        file_path = os.path.join(self.docs_dir, filename)
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info("Saved file: %s", file_path)
        return file_path

    def list_documents(self) -> List[DocumentInfo]:
        documents = []
        if not os.path.exists(self.docs_dir):
            return documents
        for filename in os.listdir(self.docs_dir):
            file_path = os.path.join(self.docs_dir, filename)
            if os.path.isfile(file_path):
                documents.append(
                    DocumentInfo(
                        document_id=os.path.splitext(filename)[0],
                        filename=filename,
                        size=os.path.getsize(file_path),
                        last_modified=os.path.getmtime(file_path),
                    )
                )
        return documents
