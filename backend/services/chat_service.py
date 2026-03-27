import json
import logging
from typing import AsyncGenerator, Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI

from core.config import Settings
from models.chat import ChatRequest, ChatResponse
from repositories.chat_repository import ChatRepository
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
        chat_repo: Optional[ChatRepository] = None,
    ):
        self.vector_repo = vector_repo
        self.image_repo = image_repo
        self.chat_repo = chat_repo
        self.llm = AzureChatOpenAI(
            azure_deployment=settings.azure_openai_llm_deployment,
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            temperature=0.7,
            streaming=True,
        )

    def _ensure_session(self, request: ChatRequest) -> str:
        """Get or create a session, return session_id."""
        if request.session_id and self.chat_repo:
            session = self.chat_repo.get_session(request.session_id)
            if session:
                return session.id
        if self.chat_repo:
            session = self.chat_repo.create_session()
            return session.id
        return ""

    def chat(self, request: ChatRequest) -> ChatResponse:
        session_id = self._ensure_session(request)

        # Save user message
        if self.chat_repo and session_id:
            self.chat_repo.add_message(session_id, "user", request.message)

        if request.use_rag and (self.vector_repo or self.image_repo):
            result = self._chat_with_rag(request)
        else:
            result = self._chat_plain(request)

        # Save bot message
        if self.chat_repo and session_id:
            self.chat_repo.add_message(session_id, "bot", result.response, result.sources)
            # Auto-title on first exchange
            if not request.session_id:
                title = request.message[:50]
                self.chat_repo.update_session_title(session_id, title)

        result.session_id = session_id
        return result

    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Stream chat response as SSE events."""
        session_id = self._ensure_session(request)

        # Save user message
        if self.chat_repo and session_id:
            self.chat_repo.add_message(session_id, "user", request.message)

        messages, sources = self._build_messages(request)

        # Send session_id and sources first
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id}, ensure_ascii=False)}\n\n"

        if sources:
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources}, ensure_ascii=False)}\n\n"

        # Stream LLM response
        full_response = ""
        async for chunk in self.llm.astream(messages):
            content = chunk.content
            if content:
                full_response += content
                yield f"data: {json.dumps({'type': 'token', 'content': content}, ensure_ascii=False)}\n\n"

        # Save bot message
        if self.chat_repo and session_id:
            self.chat_repo.add_message(session_id, "bot", full_response, sources)
            if not request.session_id:
                title = request.message[:50]
                self.chat_repo.update_session_title(session_id, title)

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    def _build_messages(self, request: ChatRequest) -> tuple:
        """Build LLM messages and return (messages, sources)."""
        if request.use_rag and (self.vector_repo or self.image_repo):
            context, sources, image_context = self._retrieve(request.message)
            template = RAG_ATTACHMENT_TEMPLATE if request.hasAttachment else RAG_TEMPLATE
            content = template.format(
                message=request.message,
                language=request.language,
                context=context or "なし",
                image_context=image_context,
            )
            return [{"role": "system", "content": content}], sources
        else:
            template = PLAIN_ATTACHMENT_TEMPLATE if request.hasAttachment else PLAIN_TEMPLATE
            content = template.format(message=request.message, language=request.language)
            return [{"role": "system", "content": content}], []

    def _retrieve(self, query: str) -> tuple:
        """Retrieve context from vector and image stores."""
        context = ""
        sources = []
        if self.vector_repo:
            docs = self.vector_repo.similarity_search(query, k=3)
            context = "\n\n".join(doc.page_content for doc in docs)
            sources = [doc.metadata.get("source", "不明なソース") for doc in docs]

        image_context = "なし"
        if self.image_repo:
            try:
                image_docs = self.image_repo.search_by_text(query, k=2)
                if image_docs:
                    image_context = "\n".join(
                        f"- {doc.metadata.get('source', '画像')}" for doc in image_docs
                    )
                    sources.extend(doc.metadata.get("source", "画像") for doc in image_docs)
            except Exception as e:
                logger.warning("Image search failed: %s", e)

        return context, sources, image_context

    def _chat_with_rag(self, request: ChatRequest) -> ChatResponse:
        messages, sources = self._build_messages(request)
        response = self.llm.invoke(messages).content
        return ChatResponse(response=response, sources=sources)

    def _chat_plain(self, request: ChatRequest) -> ChatResponse:
        messages, sources = self._build_messages(request)
        response = self.llm.invoke(messages).content
        return ChatResponse(response=response, sources=sources)
