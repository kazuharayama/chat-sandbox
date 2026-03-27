from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str


class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    size: int
    last_modified: float
