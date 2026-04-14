import json
import logging
from typing import AsyncGenerator, List, Optional

from core.config import Settings
from models.agent_config import LLMModelInfo
from repositories.agent_config_repository import AgentConfigRepository
from repositories.image_repository import ImageRepository
from repositories.vector_repository import VectorRepository
from services.llm_factory import create_llm

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = """あなたは親しみやすいAIアシスタントです。{language}で返答してください。
返答は会話的で親しみやすい口調にしてください。

{rag_section}"""

DEFAULT_RAG_SECTION = """以下の関連ドキュメントの情報も参考にしてください。ドキュメントに関連情報がない場合は無視してください。

関連ドキュメント:
{context}

関連画像:
{image_context}"""


class ContextLabService:
    def __init__(
        self,
        settings: Settings,
        vector_repo: Optional[VectorRepository],
        image_repo: Optional[ImageRepository] = None,
        agent_config_repo: Optional[AgentConfigRepository] = None,
    ):
        self.settings = settings
        self.vector_repo = vector_repo
        self.image_repo = image_repo
        self.agent_config_repo = agent_config_repo

    def _get_prompt(self, prompt_key: str, fallback: str) -> str:
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
            logger.warning("Failed to load prompt '%s': %s", prompt_key, e)
        return fallback

    def test_retrieval(self, query: str, similarity_k: int = 3, threshold: float = 0.0,
                       collection_name: str = "chat_documents") -> dict:
        """Run similarity search and return chunks with scores."""
        chunks = []

        if self.vector_repo and collection_name == "chat_documents":
            results = self.vector_repo.similarity_search_with_score(query, k=similarity_k)
            for doc, score in results:
                if threshold > 0 and score > threshold:
                    continue
                chunks.append({
                    "content": doc.page_content,
                    "score": round(float(score), 4),
                    "metadata": doc.metadata,
                })

        if self.image_repo and collection_name == "image_documents":
            results = self.image_repo.search_by_text_with_score(query, k=similarity_k)
            for doc, score in results:
                if threshold > 0 and score > threshold:
                    continue
                chunks.append({
                    "content": doc.page_content,
                    "score": round(float(score), 4),
                    "metadata": doc.metadata,
                })

        return {"chunks": chunks, "total": len(chunks), "query": query}

    def build_context_preview(self, query: str, similarity_k: int = 3,
                              threshold: float = 0.0, language: str = "日本語",
                              system_prompt_override: str = None) -> dict:
        """Build the full prompt that would be sent to the LLM, without calling it."""
        # Retrieve
        context = ""
        image_context = "なし"

        if self.vector_repo:
            results = self.vector_repo.similarity_search_with_score(query, k=similarity_k)
            docs = [(doc, score) for doc, score in results if threshold <= 0 or score <= threshold]
            context = "\n\n".join(doc.page_content for doc, _ in docs) if docs else "なし"

        if self.image_repo:
            try:
                image_docs = self.image_repo.search_by_text(query, k=2)
                if image_docs:
                    image_context = "\n".join(
                        f"- {doc.metadata.get('source', '画像')}" for doc in image_docs
                    )
            except Exception:
                pass

        # Build RAG section
        rag_template = system_prompt_override if system_prompt_override else self._get_prompt("rag_section", DEFAULT_RAG_SECTION)
        if not system_prompt_override:
            rag_section = rag_template.format(context=context or "なし", image_context=image_context)
        else:
            rag_section = rag_template

        # Build system prompt
        system_template = self._get_prompt("system_prompt", DEFAULT_SYSTEM_PROMPT)
        system_content = system_template.format(language=language, rag_section=rag_section)

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": query},
        ]

        return {
            "messages": messages,
            "token_estimate": sum(len(m["content"]) // 3 for m in messages),
        }

    async def test_chat_stream(
        self, query: str, similarity_k: int = 3, threshold: float = 0.0,
        temperature: float = 0.7, max_tokens: int = None,
        language: str = "日本語", system_prompt_override: str = None,
    ) -> AsyncGenerator[str, None]:
        """Run a test chat with parameter overrides, streaming response."""
        # Build context preview first
        preview = self.build_context_preview(
            query, similarity_k, threshold, language, system_prompt_override
        )
        messages = preview["messages"]

        # Create temporary LLM with overridden params
        llm = None
        if self.agent_config_repo:
            try:
                model = self.agent_config_repo.get_default_model()
                if model:
                    temp_model = LLMModelInfo(
                        id=model.id, name=model.name, provider=model.provider,
                        deployment_name=model.deployment_name,
                        temperature=temperature, max_tokens=max_tokens,
                        is_default=model.is_default, config=model.config,
                    )
                    llm = create_llm(temp_model, self.settings)
            except Exception as e:
                logger.warning("Failed to create test LLM: %s", e)

        if not llm:
            from langchain_ollama import ChatOllama
            llm = ChatOllama(
                model=self.settings.ollama_llm_model,
                base_url=self.settings.ollama_base_url,
                temperature=temperature,
                num_predict=max_tokens,
            )

        yield f"data: {json.dumps({'type': 'params', 'similarity_k': similarity_k, 'threshold': threshold, 'temperature': temperature, 'max_tokens': max_tokens}, ensure_ascii=False)}\n\n"

        full_response = ""
        async for chunk in llm.astream(messages):
            content = chunk.content
            if content:
                full_response += content
                yield f"data: {json.dumps({'type': 'token', 'content': content}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'total_length': len(full_response)})}\n\n"
