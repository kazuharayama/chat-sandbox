import logging
import os
from typing import List, Optional
from langchain.schema import Document
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from utils.db_connection import get_database_url
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PGVectorManager:
    def __init__(self, collection_name: str = "chat_documents"):
        self.embeddings = OpenAIEmbeddings()
        self.collection_name = collection_name
        self.connection_str = get_database_url()
        
        logger.info(f"Initializing PGVectorManager with collection: {self.collection_name}")
        
        self.pgvector_db = PGVector(
            embeddings=self.embeddings,
            collection_name=self.collection_name,
            connection=self.connection_str,
            use_jsonb=True,
        )
        
    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to vector store."""
        try:
            existing_count = self.get_existing_doc_count()
            ids = [f"doc_{existing_count + i + 1}" for i in range(len(documents))]
            
            self.pgvector_db.add_documents(documents, ids=ids)
            logger.info(f"Added {len(documents)} documents to vector store")
            return ids
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
            
    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Perform similarity search."""
        try:
            return self.pgvector_db.similarity_search(query, k=k)
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            raise
            
    def similarity_search_with_score(self, query: str, k: int = 4):
        """Perform similarity search with scores."""
        try:
            return self.pgvector_db.similarity_search_with_score(query, k=k)
        except Exception as e:
            logger.error(f"Error in similarity search with score: {e}")
            raise
    
    def get_existing_doc_count(self) -> int:
        """Get count of existing documents."""
        try:
            engine = create_engine(self.connection_str)
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT COUNT(*) FROM langchain_pg_embedding WHERE collection_id = (SELECT uuid FROM langchain_pg_collection WHERE name = :name)"),
                    {"name": self.collection_name}
                )
                count = result.scalar()
                return count or 0
        except Exception as e:
            logger.warning(f"Could not get document count, assuming 0: {e}")
            return 0
    
    def clear_collection(self):
        """Clear all documents from the collection."""
        try:
            engine = create_engine(self.connection_str)
            with engine.connect() as conn:
                # Delete documents from this collection
                conn.execute(
                    text("""
                    DELETE FROM langchain_pg_embedding 
                    WHERE collection_id = (
                        SELECT uuid FROM langchain_pg_collection WHERE name = :name
                    )
                    """),
                    {"name": self.collection_name}
                )
                # Delete the collection
                conn.execute(
                    text("DELETE FROM langchain_pg_collection WHERE name = :name"),
                    {"name": self.collection_name}
                )
                conn.commit()
                logger.info(f"Cleared collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise
    
    @classmethod
    def get_instance(cls, collection_name: str = "chat_documents") -> "PGVectorManager":
        """Get singleton instance."""
        if not hasattr(cls, '_instances'):
            cls._instances = {}
        
        if collection_name not in cls._instances:
            cls._instances[collection_name] = cls(collection_name)
            
        return cls._instances[collection_name]