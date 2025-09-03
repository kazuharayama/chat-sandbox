from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from config import get_vector_store
from routers.documents import initialize_vector_store

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    language: str = "日本語"
    hasAttachment: bool = False
    use_rag: bool = True
    
class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        vector_store = get_vector_store()
        
        if request.use_rag and vector_store is None:
            # ベクトルストアがない場合は初期化を試みる
            vector_store = initialize_vector_store()
        
        # LLMの初期化
        llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL_NAME", "gpt-4"),
            temperature=0.7
        )
        
        # 入力メッセージの処理
        input_text = request.message
        has_attachment = request.hasAttachment
        
        if request.use_rag and vector_store:
            # RAGを使用したチャット応答
            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}
            )
            
            # プロンプトテンプレート
            if has_attachment:
                template = """ユーザーが画像を添付して次のメッセージを送信しました: {message}

画像の内容については分かりませんが、画像が添付されていることを考慮して、{language}で適切に返答してください。
以下の関連ドキュメントの情報も参考にしてください。ドキュメントに関連情報がない場合は無視してください。
返答は会話的で親しみやすい口調にしてください。

関連ドキュメント:
{context}"""
            else:
                template = """ユーザーからの次のメッセージに対して、{language}で適切に返答してください: {message}

以下の関連ドキュメントの情報も参考にしてください。ドキュメントに関連情報がない場合は無視してください。
返答は会話的で親しみやすい口調にしてください。

関連ドキュメント:
{context}"""
            
            prompt = ChatPromptTemplate.from_template(template)
            
            # RAGチェーンの構築
            rag_chain = (
                {"context": retriever, "message": RunnablePassthrough(), "language": lambda _: request.language}
                | prompt
                | llm
                | StrOutputParser()
            )
            
            # ドキュメント取得と結果の生成
            docs = retriever.get_relevant_documents(input_text)
            sources = [doc.metadata.get("source", "不明なソース") for doc in docs]
            
            # RAGチェーンを実行
            config = {}
            response = rag_chain.invoke(input_text, config=config)
            
            return {"response": response, "sources": sources}
        else:
            # 通常のチャット応答
            if has_attachment:
                prompt_template = """ユーザーが画像を添付して次のメッセージを送信しました: {message}

画像の内容については分かりませんが、画像が添付されていることを考慮して、{language}で適切に返答してください。
返答は会話的で親しみやすい口調にしてください。"""
            else:
                prompt_template = """ユーザーからの次のメッセージに対して、{language}で適切に返答してください: {message}

返答は会話的で親しみやすい口調にしてください。"""
            
            prompt = ChatPromptTemplate.from_template(prompt_template)
            chain = prompt | llm | StrOutputParser()
            
            # 通常のチェーンを実行
            config = {}
            response = chain.invoke({"message": input_text, "language": request.language}, config=config)
            
            return {"response": response, "sources": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"チャット処理中にエラーが発生しました: {str(e)}")
