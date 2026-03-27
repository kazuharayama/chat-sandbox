import logging
import os
from typing import List

from azure.storage.blob import BlobServiceClient

from models.document import DocumentInfo

logger = logging.getLogger(__name__)


class DocumentRepository:
    def __init__(self, connection_string: str, container_name: str, local_cache_dir: str):
        self.container_name = container_name
        self.local_cache_dir = local_cache_dir
        os.makedirs(self.local_cache_dir, exist_ok=True)

        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client(container_name)
        logger.info("DocumentRepository initialized (container=%s)", container_name)

    async def save_file(self, content: bytes, filename: str) -> str:
        """Upload to Azure Blob Storage and cache locally for processing."""
        # Azure Blob にアップロード
        blob_client = self.container_client.get_blob_client(filename)
        blob_client.upload_blob(content, overwrite=True)
        logger.info("Uploaded to Azure Blob: %s/%s", self.container_name, filename)

        # ローカルキャッシュ（ベクトル化処理用）
        local_path = os.path.join(self.local_cache_dir, filename)
        with open(local_path, "wb") as f:
            f.write(content)

        return local_path

    def list_documents(self) -> List[DocumentInfo]:
        """List documents from Azure Blob Storage."""
        documents = []
        blobs = self.container_client.list_blobs()
        for blob in blobs:
            documents.append(
                DocumentInfo(
                    document_id=os.path.splitext(blob.name)[0],
                    filename=blob.name,
                    size=blob.size,
                    last_modified=blob.last_modified.timestamp(),
                )
            )
        return documents

    def delete_file(self, filename: str) -> None:
        """Delete from Azure Blob Storage and local cache."""
        blob_client = self.container_client.get_blob_client(filename)
        blob_client.delete_blob()
        logger.info("Deleted from Azure Blob: %s/%s", self.container_name, filename)

        local_path = os.path.join(self.local_cache_dir, filename)
        if os.path.exists(local_path):
            os.remove(local_path)

    def download_file(self, filename: str) -> str:
        """Download from Azure Blob to local cache and return local path."""
        local_path = os.path.join(self.local_cache_dir, filename)
        if os.path.exists(local_path):
            return local_path

        blob_client = self.container_client.get_blob_client(filename)
        with open(local_path, "wb") as f:
            f.write(blob_client.download_blob().readall())
        logger.info("Downloaded from Azure Blob: %s", filename)
        return local_path
