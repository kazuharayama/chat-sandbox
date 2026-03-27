import logging
from typing import Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI

from core.config import Settings
from models.chat import ChatRequest, ChatResponse
from repositories.image_repository import ImageRepository
from repositories.vector_repository import VectorRepository

logger = logging.getLogger(__name__)

RAG_TEMPLATE = """ユーザーからの次のメッセージに対して、{language}で適切に返答してください: {message}

以下の関連ドキュメントの情報も参考にしてください。ドキュメントに関連情報がない場合は無視してください。
返答は会話的で親しみやすい口調にしてください。

関連ドキュメント:
{context}

関連画像:
{image_context}"""

RAG_ATTACHMENT_TEMPLATE = """ユーザーが画像を添付して次のメッセージを送信しました: {message}

画像の内容については分かりませんが、画像が添付されていることを考慮して、{language}で適切に返答してください。
以下の関連ドキュメントの情報も参考にしてください。ドキュメントに関連情報がない場合は無視してください。
返答は会話的で親しみやすい口調にしてください。

関連ドキュメント:
{context}

関連画像:
{image_context}"""

PLAIN_TEMPLATE = """ユーザーからの次のメッセージに対して、{language}で適切に返答してください: {message}

返答は会話的で親しみやすい口調にしてください。"""

PLAIN_ATTACHMENT_TEMPLATE = """ユーザーが画像を添付して次のメッセージを送信しました: {message}

画像の内容については分かりませんが、画像が添付されていることを考慮して、{language}で適切に返答してください。
返答は会話的で親しみやすい口調にしてください。"""


class ChatService:
    def __init__(
        self,
        settings: Settings,
        vector_repo: Optional[VectorRepository],
        image_repo: Optional[ImageRepository] = None,
    ):
        self.vector_repo = vector_repo
        self.image_repo = image_repo
        self.llm = AzureChatOpenAI(
            azure_deployment=settings.azure_openai_llm_deployment,
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            temperature=0.7,
        )

    def chat(self, request: ChatRequest) -> ChatResponse:
        if request.use_rag and (self.vector_repo or self.image_repo):
            return self._chat_with_rag(request)
        return self._chat_plain(request)

    def _chat_with_rag(self, request: ChatRequest) -> ChatResponse:
        # テキスト文書検索
        context = ""
        sources = []
        if self.vector_repo:
            docs = self.vector_repo.similarity_search(request.message, k=3)
            context = "\n\n".join(doc.page_content for doc in docs)
            sources = [doc.metadata.get("source", "不明なソース") for doc in docs]

        # 画像検索 (CLIP)
        image_context = "なし"
        if self.image_repo:
            try:
                image_docs = self.image_repo.search_by_text(request.message, k=2)
                if image_docs:
                    image_context = "\n".join(
                        f"- {doc.metadata.get('source', '画像')}" for doc in image_docs
                    )
                    sources.extend(doc.metadata.get("source", "画像") for doc in image_docs)
            except Exception as e:
                logger.warning("Image search failed: %s", e)

        template = RAG_ATTACHMENT_TEMPLATE if request.hasAttachment else RAG_TEMPLATE
        response = self.llm.invoke(
            [{"role": "system", "content": template.format(
                message=request.message,
                language=request.language,
                context=context or "なし",
                image_context=image_context,
            )}]
        ).content

        return ChatResponse(response=response, sources=sources)

    def _chat_plain(self, request: ChatRequest) -> ChatResponse:
        template = PLAIN_ATTACHMENT_TEMPLATE if request.hasAttachment else PLAIN_TEMPLATE
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({"message": request.message, "language": request.language})
        return ChatResponse(response=response, sources=[])
