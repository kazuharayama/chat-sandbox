import logging
from functools import lru_cache
from typing import Optional

from core.config import Settings, get_settings
from repositories.document_repository import DocumentRepository
from repositories.vector_repository import VectorRepository
from services.chat_service import ChatService
from services.document_service import DocumentService

logger = logging.getLogger(__name__)

_vector_repo: Optional[VectorRepository] = None
_document_repo: Optional[DocumentRepository] = None
_chat_service: Optional[ChatService] = None
_document_service: Optional[DocumentService] = None


def init_dependencies(settings: Settings) -> None:
    """Initialize all dependencies at startup."""
    global _vector_repo, _document_repo, _chat_service, _document_service

    # Repositories
    try:
        _vector_repo = VectorRepository(settings)
        logger.info("VectorRepository initialized")
    except Exception as e:
        logger.warning("Failed to initialize VectorRepository: %s", e)
        _vector_repo = None

    _document_repo = DocumentRepository(settings.docs_dir)

    # Services
    _chat_service = ChatService(settings, _vector_repo)
    _document_service = DocumentService(_document_repo, _vector_repo)

    logger.info("All dependencies initialized")


def get_chat_service() -> ChatService:
    return _chat_service


def get_document_service() -> DocumentService:
    return _document_service
