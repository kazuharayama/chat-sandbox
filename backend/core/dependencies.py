import logging
from typing import Optional

from core.config import Settings
from repositories.agent_config_repository import AgentConfigRepository
from repositories.chat_repository import ChatRepository
from repositories.document_repository import DocumentRepository
from repositories.image_repository import ImageRepository
from repositories.vector_repository import VectorRepository
from services.chat_service import ChatService
from services.document_service import DocumentService

logger = logging.getLogger(__name__)

_vector_repo: Optional[VectorRepository] = None
_image_repo: Optional[ImageRepository] = None
_document_repo: Optional[DocumentRepository] = None
_chat_repo: Optional[ChatRepository] = None
_agent_config_repo: Optional[AgentConfigRepository] = None
_chat_service: Optional[ChatService] = None
_document_service: Optional[DocumentService] = None


def init_dependencies(settings: Settings) -> None:
    """Initialize all dependencies at startup."""
    global _vector_repo, _image_repo, _document_repo, _chat_repo, _agent_config_repo, _chat_service, _document_service

    # Repositories
    try:
        _vector_repo = VectorRepository(settings)
        logger.info("VectorRepository initialized")
    except Exception as e:
        logger.warning("Failed to initialize VectorRepository: %s", e)
        _vector_repo = None

    try:
        _image_repo = ImageRepository(settings)
        logger.info("ImageRepository initialized")
    except Exception as e:
        logger.warning("Failed to initialize ImageRepository: %s", e)
        _image_repo = None

    _document_repo = DocumentRepository(
        connection_string=settings.azure_storage_connection_string,
        container_name=settings.azure_storage_container_name,
        local_cache_dir=settings.docs_dir,
    )

    _chat_repo = ChatRepository(settings.database_url)
    _agent_config_repo = AgentConfigRepository(settings.database_url)

    # Services
    _chat_service = ChatService(settings, _vector_repo, _image_repo, _chat_repo)
    _document_service = DocumentService(_document_repo, _vector_repo, _image_repo)

    logger.info("All dependencies initialized")


def get_chat_service() -> ChatService:
    return _chat_service


def get_document_service() -> DocumentService:
    return _document_service


def get_chat_repository() -> ChatRepository:
    return _chat_repo


def get_agent_config_repository() -> AgentConfigRepository:
    return _agent_config_repo
