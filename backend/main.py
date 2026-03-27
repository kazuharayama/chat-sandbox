from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from core.dependencies import init_dependencies
from core.logging import setup_logging
from routers import chat, documents, sessions


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()
    init_dependencies(settings)
    yield


app = FastAPI(title="LangChain RAGシステム", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, tags=["chat"])
app.include_router(documents.router, tags=["documents"])
app.include_router(sessions.router)


@app.get("/")
def health_check():
    return {"message": "LangChain RAGシステムへようこそ！"}
