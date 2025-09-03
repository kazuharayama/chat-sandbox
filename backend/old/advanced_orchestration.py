from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage
from langchain.chains import create_extraction_chain
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv
import os

# 環境変数の読み込み
load_dotenv()

# カスタムツールの定義
@tool
def search_database(query: str) -> str:
    """データベースを検索して情報を取得します。"""
    # 実際のアプリケーションではここでデータベース検索を行います
    return f"「{query}」に関する情報がデータベースから見つかりました。"

@tool
def calculate_statistics(numbers: str) -> str:
    """数値のリストの統計情報（平均、最大、最小）を計算します。"""
    try:
        num_list = [float(n.strip()) for n in numbers.split(",")]
        avg = sum(num_list) / len(num_list)
        return f"統計情報: 平均={avg:.2f}, 最大={max(num_list)}, 最小={min(num_list)}"
    except:
        return "エラー: 有効なカンマ区切りの数値リストを入力してください"

@tool
def translate_text(text: str, target_language: str) -> str:
    """テキストを指定された言語に翻訳します。"""
    # 実際のアプリケーションでは翻訳APIを使用します
    return f"「{text}」を{target_language}に翻訳しました: 「{text} (翻訳済み)」"

# エージェントの設定
def create_agent():
    llm = ChatOpenAI(temperature=0)
    
    tools = [search_database, calculate_statistics, translate_text]
    
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "あなたは便利なAIアシスタントです。ユーザーの質問に答えるために、提供されたツールを使用してください。"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_openai_tools_agent(llm, tools, prompt)
    
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True
    )
    
    return agent_executor

# 構造化データ抽出のための定義
class Person(BaseModel):
    name: str = Field(description="人物の名前")
    age: Optional[int] = Field(description="人物の年齢")
    occupation: Optional[str] = Field(description="人物の職業")

def extract_person_info(text):
    llm = ChatOpenAI(temperature=0)
    chain = create_extraction_chain(Person, llm)
    return chain.run(text)

# マルチステップのワークフロー例
def multi_step_workflow(query: str):
    llm = ChatOpenAI(temperature=0)
    
    # ステップ1: クエリの分類
    classification_prompt = ChatPromptTemplate.from_template(
        "次のクエリを「検索」、「計算」、「翻訳」、「その他」のいずれかに分類してください: {query}"
    )
    classification_chain = classification_prompt | llm
    category = classification_chain.invoke({"query": query})
    
    # ステップ2: カテゴリに基づいた処理
    if "検索" in category:
        result = search_database(query)
    elif "計算" in category:
        result = calculate_statistics(query)
    elif "翻訳" in category:
        # 翻訳先言語の抽出
        language_prompt = ChatPromptTemplate.from_template(
            "次のクエリから翻訳先の言語を抽出してください: {query}"
        )
        language_chain = language_prompt | llm
        target_language = language_chain.invoke({"query": query})
        
        # テキスト部分の抽出
        text_prompt = ChatPromptTemplate.from_template(
            "次のクエリから翻訳すべきテキスト部分を抽出してください: {query}"
        )
        text_chain = text_prompt | llm
        text = text_chain.invoke({"query": query})
        
        result = translate_text(text, target_language)
    else:
        # 一般的な応答
        general_prompt = ChatPromptTemplate.from_template(
            "次の質問に日本語で答えてください: {query}"
        )
        general_chain = general_prompt | llm
        result = general_chain.invoke({"query": query})
    
    # ステップ3: 結果のフォーマット
    format_prompt = ChatPromptTemplate.from_template(
        "次の結果を読みやすくフォーマットしてください: {result}"
    )
    format_chain = format_prompt | llm
    formatted_result = format_chain.invoke({"result": result})
    
    return formatted_result

# 使用例
if __name__ == "__main__":
    # エージェントの使用例
    agent = create_agent()
    agent_result = agent.invoke({"input": "1, 5, 9, 2, 8, 3 の統計情報を教えてください"})
    print("エージェント結果:", agent_result)
    
    # 構造化データ抽出の例
    extraction_result = extract_person_info("山田太郎は45歳のエンジニアです。")
    print("抽出結果:", extraction_result)
    
    # マルチステップワークフローの例
    workflow_result = multi_step_workflow("「こんにちは」を英語に翻訳して")
    print("ワークフロー結果:", workflow_result)
