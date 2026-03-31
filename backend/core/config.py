import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Azure OpenAI
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-08-01-preview"
    azure_openai_llm_deployment: str = "gpt-4o"
    azure_openai_embedding_deployment: str = "text-embedding-ada-002"

    # Database
    db_host: str = "localhost"
    db_name: str = "chat_db"
    db_user: str = "chat_user"
    db_password: str = "chat_pass"
    db_port: int = 5432

    # Azure Blob Storage
    azure_storage_connection_string: str = ""
    azure_storage_container_name: str = "documents"

    # Entra ID
    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""
    azure_allowed_group_id: str = ""
    azure_admin_group_id: str = ""

    # Langfuse
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = ""

    # Speech (STT/TTS)
    whisper_model_size: str = "base"
    whisper_language: str = "ja"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    piper_model_path: str = "/app/models/piper/ja_JP-amitaro-medium.onnx"
    piper_config_path: str = "/app/models/piper/ja_JP-amitaro-medium.onnx.json"

    # App
    docs_dir: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")

    @property
    def database_url(self) -> str:
        return f"postgresql+psycopg2://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
