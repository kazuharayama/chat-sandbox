from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import documents, chat, speech
from utils.pgvector_manager import PGVectorManager

# FastAPIアプリケーションの設定
app = FastAPI(title="LangChain RAGシステム")

# CORS設定を追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では特定のオリジンのみを許可するように変更すべき
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの登録
app.include_router(documents.router, tags=["documents"])
app.include_router(chat.router, tags=["chat"])
app.include_router(speech.router, tags=["speech"])

# アプリ起動時にPGVectorを初期化
@app.on_event("startup")
async def startup_event():
    try:
        # PGVectorManagerの初期化
        PGVectorManager.get_instance()
        print("PGVector initialized successfully")
    except Exception as e:
        print(f"Warning: Failed to initialize PGVector: {e}")
        print("The application will continue without vector search functionality")

@app.get("/")
def read_root():
    return {"message": "LangChain RAGシステムへようこそ！"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
