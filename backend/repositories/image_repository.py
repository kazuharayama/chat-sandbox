import logging
from typing import List, Tuple

from langchain_postgres import PGVector
from langchain.schema import Document

from core.config import Settings
from infrastructure.clip_embeddings import CLIPImageEncoder, CLIPTextEmbeddings

logger = logging.getLogger(__name__)


class ImageRepository:
    """CLIP-based image vector store (separate collection from text docs)."""

    def __init__(self, settings: Settings, collection_name: str = "image_documents"):
        self.collection_name = collection_name
        self.connection_str = settings.database_url

        # CLIP text embeddings for pgvector store (used for text query search)
        self.clip_text_embeddings = CLIPTextEmbeddings()

        # CLIP image encoder (used for indexing images)
        self.image_encoder = CLIPImageEncoder()

        self.store = PGVector(
            embeddings=self.clip_text_embeddings,
            collection_name=self.collection_name,
            connection=self.connection_str,
            use_jsonb=True,
        )
        logger.info("ImageRepository initialized (collection=%s)", self.collection_name)

    def add_image(self, image_path: str, document_id: str, metadata: dict = None) -> str:
        """Encode image with CLIP and store in pgvector."""
        embedding = self.image_encoder.encode_image(image_path)

        doc_metadata = {
            "document_id": document_id,
            "source": image_path,
            "type": "image",
            **(metadata or {}),
        }

        doc = Document(
            page_content=f"[Image: {image_path}]",
            metadata=doc_metadata,
        )

        # Store with pre-computed CLIP image embedding
        self.store.add_embeddings(
            texts=[doc.page_content],
            embeddings=[embedding],
            metadatas=[doc_metadata],
            ids=[f"img_{document_id}"],
        )
        logger.info("Image indexed: %s", document_id)
        return document_id

    def search_by_text(self, query: str, k: int = 3) -> List[Document]:
        """Search images using text query (CLIP text encoder)."""
        return self.store.similarity_search(query, k=k)

    def search_by_text_with_score(self, query: str, k: int = 3) -> List[Tuple[Document, float]]:
        """Search images with similarity scores."""
        return self.store.similarity_search_with_score(query, k=k)
