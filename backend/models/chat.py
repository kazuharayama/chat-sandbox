from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    language: str = "日本語"
    hasAttachment: bool = False
    use_rag: bool = True


class ChatResponse(BaseModel):
    response: str
    sources: list[str] = []
