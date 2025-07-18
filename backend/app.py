from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from typing import List, Dict, Any, Optional
import base64
from io import BytesIO

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import SequentialChain, LLMChain
from langchain_core.output_parsers import JsonOutputParser

# 環境変数の読み込み
load_dotenv()

# APIキーの確認
if not os.getenv("OPENAI_API_KEY"):
    print("警告: OPENAI_API_KEYが設定されていません。.envファイルに設定してください。")

app = FastAPI(title="LangChain オーケストレーションアプリ")

# CORS設定を追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では特定のオリジンのみを許可するように変更すべき
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    language: str = "日本語"

class QueryResponse(BaseModel):
    summary: str
    keywords: List[str]
    sentiment: str
    next_steps: List[str]
    
class ChatRequest(BaseModel):
    message: str
    language: str = "日本語"
    hasAttachment: bool = False
    
class ChatResponse(BaseModel):
    response: str

@app.get("/")
def read_root():
    return {"message": "LangChain オーケストレーションアプリへようこそ！"}

@app.post("/analyze", response_model=QueryResponse)
def analyze_text(request: QueryRequest):
    try:
        # LLMの初期化
        llm = ChatOpenAI(temperature=0)
        
        # 要約チェーン
        summary_prompt = ChatPromptTemplate.from_template(
            "次のテキストを{language}で簡潔に要約してください: {query}"
        )
        summary_chain = LLMChain(
            llm=llm,
            prompt=summary_prompt,
            output_key="summary"
        )
        
        # キーワード抽出チェーン
        keyword_prompt = ChatPromptTemplate.from_template(
            "次のテキストから重要なキーワードを{language}で5つ抽出し、リスト形式で返してください: {query}"
        )
        keyword_chain = LLMChain(
            llm=llm,
            prompt=keyword_prompt,
            output_key="keywords_text"
        )
        
        # 感情分析チェーン
        sentiment_prompt = ChatPromptTemplate.from_template(
            "次のテキストの感情（ポジティブ、ネガティブ、ニュートラル）を{language}で分析してください: {query}"
        )
        sentiment_chain = LLMChain(
            llm=llm,
            prompt=sentiment_prompt,
            output_key="sentiment"
        )
        
        # 次のステップ提案チェーン
        next_steps_prompt = ChatPromptTemplate.from_template(
            "次のテキストに基づいて、ユーザーが次に取るべき行動を{language}で3つ提案してください: {query}\n要約: {summary}"
        )
        next_steps_chain = LLMChain(
            llm=llm,
            prompt=next_steps_prompt,
            output_key="next_steps_text"
        )
        
        # チェーンの連結
        chain = SequentialChain(
            chains=[summary_chain, keyword_chain, sentiment_chain, next_steps_chain],
            input_variables=["query", "language"],
            output_variables=["summary", "keywords_text", "sentiment", "next_steps_text"],
            verbose=True
        )
        
        # チェーンの実行
        result = chain({"query": request.query, "language": request.language})
        
        # キーワードと次のステップをリストに変換
        keywords = [keyword.strip() for keyword in result["keywords_text"].replace("- ", "").split("\n") if keyword.strip()]
        next_steps = [step.strip() for step in result["next_steps_text"].replace("- ", "").split("\n") if step.strip()]
        
        return {
            "summary": result["summary"],
            "keywords": keywords,
            "sentiment": result["sentiment"],
            "next_steps": next_steps
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析中にエラーが発生しました: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # LLMの初期化
        llm = ChatOpenAI(temperature=0.7)
        
        # 入力メッセージの処理
        input_text = request.message
        has_attachment = request.hasAttachment
        
        # プロンプトの作成
        if has_attachment:
            prompt_template = """ユーザーが画像を添付して次のメッセージを送信しました: {message}

画像の内容については分かりませんが、画像が添付されていることを考慮して、{language}で適切に返答してください。
返答は会話的で親しみやすい口調にしてください。"""
        else:
            prompt_template = """ユーザーからの次のメッセージに対して、{language}で適切に返答してください: {message}

返答は会話的で親しみやすい口調にしてください。"""
        
        chat_prompt = ChatPromptTemplate.from_template(prompt_template)
        
        # チェーンの作成と実行
        chat_chain = LLMChain(llm=llm, prompt=chat_prompt)
        result = chat_chain({"message": input_text, "language": request.language})
        
        return {"response": result["text"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"チャット処理中にエラーが発生しました: {str(e)}")

@app.post("/speech-to-text")
async def speech_to_text(audio: UploadFile = File(...)):
    try:
        # 実際の実装では、ここで音声ファイルを処理して
        # 音声認識APIを使用してテキストに変換します
        # 例: Whisper APIなど
        
        # このサンプルでは、単にダミーレスポンスを返します
        return {"text": "音声認識されたテキストがここに表示されます"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"音声認識中にエラーが発生しました: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
