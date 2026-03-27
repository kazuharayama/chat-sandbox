import logging
from typing import List

from langchain.schema import Document
from langchain_openai import AzureOpenAIEmbeddings
from langchain_postgres import PGVector
from sqlalchemy import create_engine, text

from core.config import Settings

logger = logging.getLogger(__name__)


class VectorRepository:
    def __init__(self, settings: Settings, collection_name: str = "chat_documents"):
        self.collection_name = collection_name
        self.connection_str = settings.database_url

        self.embeddings = AzureOpenAIEmbeddings(
            azure_deployment=settings.azure_openai_embedding_deployment,
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
        )

        self.store = PGVector(
            embeddings=self.embeddings,
            collection_name=self.collection_name,
            connection=self.connection_str,
            use_jsonb=True,
        )
        logger.info("VectorRepository initialized (collection=%s)", self.collection_name)

    def add_documents(self, documents: List[Document]) -> List[str]:
        existing_count = self._get_count()
        ids = [f"doc_{existing_count + i + 1}" for i in range(len(documents))]
        self.store.add_documents(documents, ids=ids)
        logger.info("Added %d documents to vector store", len(documents))
        return ids

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        return self.store.similarity_search(query, k=k)

    def similarity_search_with_score(self, query: str, k: int = 4):
        return self.store.similarity_search_with_score(query, k=k)

    def clear_collection(self) -> None:
        engine = create_engine(self.connection_str)
        with engine.connect() as conn:
            conn.execute(
                text(
                    "DELETE FROM langchain_pg_embedding "
                    "WHERE collection_id = (SELECT uuid FROM langchain_pg_collection WHERE name = :name)"
                ),
                {"name": self.collection_name},
            )
            conn.execute(
                text("DELETE FROM langchain_pg_collection WHERE name = :name"),
                {"name": self.collection_name},
            )
            conn.commit()
        logger.info("Cleared collection: %s", self.collection_name)

    def _get_count(self) -> int:
        try:
            engine = create_engine(self.connection_str)
            with engine.connect() as conn:
                result = conn.execute(
                    text(
                        "SELECT COUNT(*) FROM langchain_pg_embedding "
                        "WHERE collection_id = (SELECT uuid FROM langchain_pg_collection WHERE name = :name)"
                    ),
                    {"name": self.collection_name},
                )
                return result.scalar() or 0
        except Exception:
            logger.warning("Could not get document count, assuming 0")
            return 0
