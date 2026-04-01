"""
Search Agent: Agentic RAG with Plan → Retrieve → Evaluate → Answer cycle.

Uses LangGraph StateGraph to orchestrate multi-step retrieval.
"""
import json
import logging
from typing import Any, AsyncGenerator, Optional

from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph, END

from repositories.agent_config_repository import AgentConfigRepository
from repositories.vector_repository import VectorRepository
from repositories.image_repository import ImageRepository

logger = logging.getLogger(__name__)

# Default prompts (used if DB has no data)
DEFAULT_PLAN_PROMPT = """ユーザーの質問を分析し、効果的な検索クエリに分解してください。
質問が単純なら1つ、複雑なら2-3個のサブクエリを生成してください。

質問: {query}

JSON形式で回答してください:
{{"sub_queries": ["クエリ1", "クエリ2"]}}"""

DEFAULT_EVALUATE_PROMPT = """以下の検索結果がユーザーの質問に十分な情報を含んでいるか判定してください。

質問: {query}
検索結果:
{context}

JSON形式で回答してください:
{{"sufficient": true/false, "reason": "判定理由"}}"""

DEFAULT_ANSWER_PROMPT = """以下の情報を基に、ユーザーの質問に{language}で回答してください。
情報が不足している場合は、その旨を伝えてください。

関連ドキュメント:
{context}

質問: {query}"""


class SearchAgentState(dict):
    """State for the search agent graph."""
    query: str
    sub_queries: list[str]
    retrieved_docs: list[dict]
    context: str
    sources: list[str]
    evaluation: dict
    answer: str
    iteration: int
    max_iterations: int
    language: str
    steps: list[dict]  # SSE step events


def create_search_agent(
    llm: BaseChatModel,
    vector_repo: Optional[VectorRepository],
    image_repo: Optional[ImageRepository],
    agent_config_repo: Optional[AgentConfigRepository],
    similarity_k: int = 3,
    max_iterations: int = 2,
):
    """Create a LangGraph-based search agent."""

    def _get_prompt(key: str, fallback: str) -> str:
        if not agent_config_repo:
            return fallback
        try:
            agent = agent_config_repo.get_agent_by_name("search_agent")
            if not agent:
                return fallback
            prompt = agent_config_repo.get_active_prompt(agent.id, key)
            return prompt.content if prompt else fallback
        except Exception:
            return fallback

    def plan_node(state: dict) -> dict:
        """Decompose query into sub-queries."""
        query = state["query"]
        prompt = _get_prompt("plan_prompt", DEFAULT_PLAN_PROMPT)
        formatted = prompt.format(query=query)

        try:
            result = llm.invoke(formatted)
            content = result.content
            # Parse JSON from response
            parsed = json.loads(content) if "{" in content else {"sub_queries": [query]}
            sub_queries = parsed.get("sub_queries", [query])
        except Exception as e:
            logger.warning("Plan failed, using original query: %s", e)
            sub_queries = [query]

        step = {"step": "plan", "detail": f"クエリを{len(sub_queries)}個のサブクエリに分解しました"}
        return {
            "sub_queries": sub_queries,
            "steps": state.get("steps", []) + [step],
        }

    def retrieve_node(state: dict) -> dict:
        """Retrieve documents for all sub-queries."""
        sub_queries = state.get("sub_queries", [state["query"]])
        all_docs = []
        all_sources = []
        seen_contents = set()

        for sq in sub_queries:
            if vector_repo:
                docs = vector_repo.similarity_search(sq, k=similarity_k)
                for doc in docs:
                    if doc.page_content not in seen_contents:
                        seen_contents.add(doc.page_content)
                        all_docs.append({
                            "content": doc.page_content,
                            "source": doc.metadata.get("source", "不明"),
                        })
                        all_sources.append(doc.metadata.get("source", "不明なソース"))

        context = "\n\n".join(d["content"] for d in all_docs)
        step = {"step": "retrieve", "detail": f"{len(all_docs)}件のチャンクを取得しました"}

        return {
            "retrieved_docs": all_docs,
            "context": context,
            "sources": all_sources,
            "steps": state.get("steps", []) + [step],
        }

    def evaluate_node(state: dict) -> dict:
        """Evaluate if retrieved docs are sufficient."""
        query = state["query"]
        context = state.get("context", "")
        iteration = state.get("iteration", 0)

        if not context.strip():
            step = {"step": "evaluate", "detail": "検索結果が空です。再検索します"}
            return {
                "evaluation": {"sufficient": False, "reason": "検索結果なし"},
                "iteration": iteration + 1,
                "steps": state.get("steps", []) + [step],
            }

        prompt = _get_prompt("evaluate_prompt", DEFAULT_EVALUATE_PROMPT)
        formatted = prompt.format(query=query, context=context[:2000])

        try:
            result = llm.invoke(formatted)
            content = result.content
            parsed = json.loads(content) if "{" in content else {"sufficient": True}
            sufficient = parsed.get("sufficient", True)
        except Exception as e:
            logger.warning("Evaluation failed, assuming sufficient: %s", e)
            sufficient = True

        if sufficient:
            step = {"step": "evaluate", "detail": "十分な情報が揃いました"}
        else:
            step = {"step": "evaluate", "detail": "追加検索が必要です"}

        return {
            "evaluation": {"sufficient": sufficient},
            "iteration": iteration + 1,
            "steps": state.get("steps", []) + [step],
        }

    def answer_node(state: dict) -> dict:
        """Generate final answer from retrieved context."""
        query = state["query"]
        context = state.get("context", "情報が見つかりませんでした。")
        language = state.get("language", "日本語")

        prompt = _get_prompt("answer_prompt", DEFAULT_ANSWER_PROMPT)
        formatted = prompt.format(query=query, context=context, language=language)

        result = llm.invoke(formatted)
        step = {"step": "answer", "detail": "回答を生成しました"}

        return {
            "answer": result.content,
            "steps": state.get("steps", []) + [step],
        }

    def should_continue(state: dict) -> str:
        """Decide whether to re-retrieve or answer."""
        evaluation = state.get("evaluation", {})
        iteration = state.get("iteration", 0)
        max_iter = state.get("max_iterations", max_iterations)

        if evaluation.get("sufficient", True) or iteration >= max_iter:
            return "answer"
        return "retrieve"

    # Build the graph
    graph = StateGraph(dict)
    graph.add_node("plan", plan_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("evaluate", evaluate_node)
    graph.add_node("answer", answer_node)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "retrieve")
    graph.add_edge("retrieve", "evaluate")
    graph.add_conditional_edges("evaluate", should_continue, {"retrieve": "retrieve", "answer": "answer"})
    graph.add_edge("answer", END)

    return graph.compile()


async def run_search_agent_stream(
    llm: BaseChatModel,
    query: str,
    vector_repo: Optional[VectorRepository],
    image_repo: Optional[ImageRepository],
    agent_config_repo: Optional[AgentConfigRepository],
    similarity_k: int = 3,
    max_iterations: int = 2,
    language: str = "日本語",
) -> AsyncGenerator[str, None]:
    """Run the search agent and yield SSE events for each step."""

    agent = create_search_agent(
        llm, vector_repo, image_repo, agent_config_repo,
        similarity_k=similarity_k, max_iterations=max_iterations,
    )

    initial_state = {
        "query": query,
        "sub_queries": [],
        "retrieved_docs": [],
        "context": "",
        "sources": [],
        "evaluation": {},
        "answer": "",
        "iteration": 0,
        "max_iterations": max_iterations,
        "language": language,
        "steps": [],
    }

    # Track steps already emitted
    emitted_steps = 0

    # Run graph
    result = None
    async for state in agent.astream(initial_state):
        # state is a dict of {node_name: node_output}
        for node_name, node_output in state.items():
            if not isinstance(node_output, dict):
                continue
            steps = node_output.get("steps", [])
            # Emit new steps
            for step in steps[emitted_steps:]:
                yield f"data: {json.dumps({'type': 'step', **step}, ensure_ascii=False)}\n\n"
            emitted_steps = len(steps)
            result = node_output

    # Emit sources
    sources = result.get("sources", []) if result else []
    if sources:
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources}, ensure_ascii=False)}\n\n"

    # Stream the answer as tokens
    answer = result.get("answer", "") if result else ""
    # Send answer in chunks to simulate streaming
    chunk_size = 10
    for i in range(0, len(answer), chunk_size):
        chunk = answer[i:i + chunk_size]
        yield f"data: {json.dumps({'type': 'token', 'content': chunk}, ensure_ascii=False)}\n\n"
