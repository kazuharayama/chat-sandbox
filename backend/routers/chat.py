from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from utils.pgvector_manager import PGVectorManager
from config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_LLM_DEPLOYMENT,
)

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
        vector_manager = None
        
        if request.use_rag:
            try:
                vector_manager = PGVectorManager.get_instance()
            except Exception as e:
                print(f"Error initializing PGVector: {e}")
                vector_manager = None
        
        # LLMの初期化（Azure OpenAI）
        llm = AzureChatOpenAI(
            azure_deployment=AZURE_OPENAI_LLM_DEPLOYMENT,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            temperature=0.7,
        )
        
        # 入力メッセージの処理
        input_text = request.message
        has_attachment = request.hasAttachment
        
        if request.use_rag and vector_manager:
            # RAGを使用したチャット応答
            try:
                # PGVectorで類似度検索を実行
                docs = vector_manager.similarity_search(input_text, k=3)
                
                # コンテキストを作成
                context = "\n\n".join([doc.page_content for doc in docs])
                sources = [doc.metadata.get("source", "不明なソース") for doc in docs]
            except Exception as e:
                print(f"Error in similarity search: {e}")
                docs = []
                context = ""
                sources = []
            
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
            
            # プロンプトにコンテキストを直接渡す
            response = llm.invoke([
                {"role": "system", "content": template.format(
                    message=input_text,
                    language=request.language, 
                    context=context
                )}
            ]).content
            
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
