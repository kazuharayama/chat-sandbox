from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import documents, chat, speech
from routers.documents import initialize_vector_store

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

# アプリ起動時にベクトルストアを初期化
@app.on_event("startup")
async def startup_event():
    initialize_vector_store()

@app.get("/")
def read_root():
    return {"message": "LangChain RAGシステムへようこそ！"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
