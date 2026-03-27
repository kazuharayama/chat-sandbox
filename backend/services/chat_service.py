import json
import logging
from typing import AsyncGenerator, List, Optional

from langchain_openai import AzureChatOpenAI

from core.config import Settings
from models.chat import ChatRequest, ChatResponse
from repositories.agent_config_repository import AgentConfigRepository
from repositories.chat_repository import ChatRepository
from repositories.image_repository import ImageRepository
from repositories.vector_repository import VectorRepository

logger = logging.getLogger(__name__)

# Fallback prompts (used if DB has no data)
DEFAULT_SYSTEM_PROMPT = """あなたは親しみやすいAIアシスタントです。{language}で返答してください。
返答は会話的で親しみやすい口調にしてください。

{rag_section}"""

DEFAULT_RAG_SECTION = """以下の関連ドキュメントの情報も参考にしてください。ドキュメントに関連情報がない場合は無視してください。

関連ドキュメント:
{context}

関連画像:
{image_context}"""

MAX_HISTORY_MESSAGES = 20


class ChatService:
    def __init__(
        self,
        settings: Settings,
        vector_repo: Optional[VectorRepository],
        image_repo: Optional[ImageRepository] = None,
        chat_repo: Optional[ChatRepository] = None,
        agent_config_repo: Optional[AgentConfigRepository] = None,
    ):
        self.vector_repo = vector_repo
        self.image_repo = image_repo
        self.chat_repo = chat_repo
        self.agent_config_repo = agent_config_repo
        self.llm = AzureChatOpenAI(
            azure_deployment=settings.azure_openai_llm_deployment,
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            temperature=0.7,
            streaming=True,
        )

    def _get_prompt(self, prompt_key: str, fallback: str) -> str:
        """Get prompt from DB, fallback to hardcoded default."""
        if not self.agent_config_repo:
            return fallback
        try:
            agent = self.agent_config_repo.get_agent_by_name("assistant")
            if not agent:
                return fallback
            prompt = self.agent_config_repo.get_active_prompt(agent.id, prompt_key)
            if prompt:
                return prompt.content
        except Exception as e:
            logger.warning("Failed to load prompt '%s' from DB: %s", prompt_key, e)
        return fallback

    def _ensure_session(self, request: ChatRequest) -> str:
        if request.session_id and self.chat_repo:
            session = self.chat_repo.get_session(request.session_id)
            if session:
                return session.id
        if self.chat_repo:
            session = self.chat_repo.create_session()
            return session.id
        return ""

    def _get_history(self, session_id: str) -> List[dict]:
        if not self.chat_repo or not session_id:
            return []
        messages = self.chat_repo.get_messages(session_id)
        recent = messages[-(MAX_HISTORY_MESSAGES + 1):-1] if len(messages) > 1 else []
        return [
            {"role": "user" if m.role == "user" else "assistant", "content": m.content}
            for m in recent
        ]

    def _build_messages(self, request: ChatRequest, session_id: str = "") -> tuple:
        sources = []
        rag_section = ""

        if request.use_rag and (self.vector_repo or self.image_repo):
            context, sources, image_context = self._retrieve(request.message)
            rag_template = self._get_prompt("rag_section", DEFAULT_RAG_SECTION)
            rag_section = rag_template.format(
                context=context or "なし",
                image_context=image_context,
            )

        system_template = self._get_prompt("system_prompt", DEFAULT_SYSTEM_PROMPT)
        system_content = system_template.format(
            language=request.language,
            rag_section=rag_section,
        )

        messages = [{"role": "system", "content": system_content}]
        history = self._get_history(session_id)
        messages.extend(history)
        messages.append({"role": "user", "content": request.message})

        return messages, sources

    def chat(self, request: ChatRequest) -> ChatResponse:
        session_id = self._ensure_session(request)

        if self.chat_repo and session_id:
            self.chat_repo.add_message(session_id, "user", request.message)

        messages, sources = self._build_messages(request, session_id)
        response = self.llm.invoke(messages).content

        if self.chat_repo and session_id:
            self.chat_repo.add_message(session_id, "bot", response, sources)
            if not request.session_id:
                self.chat_repo.update_session_title(session_id, request.message[:50])

        return ChatResponse(response=response, sources=sources, session_id=session_id)

    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        session_id = self._ensure_session(request)

        if self.chat_repo and session_id:
            self.chat_repo.add_message(session_id, "user", request.message)

        messages, sources = self._build_messages(request, session_id)

        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id}, ensure_ascii=False)}\n\n"

        if sources:
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources}, ensure_ascii=False)}\n\n"

        full_response = ""
        async for chunk in self.llm.astream(messages):
            content = chunk.content
            if content:
                full_response += content
                yield f"data: {json.dumps({'type': 'token', 'content': content}, ensure_ascii=False)}\n\n"

        if self.chat_repo and session_id:
            self.chat_repo.add_message(session_id, "bot", full_response, sources)
            if not request.session_id:
                self.chat_repo.update_session_title(session_id, request.message[:50])

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    def _retrieve(self, query: str) -> tuple:
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
