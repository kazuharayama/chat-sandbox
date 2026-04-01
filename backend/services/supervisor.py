"""
Supervisor: Routes user queries to the appropriate agent based on routing_rules.
"""
import json
import logging
from typing import Optional

from langchain_core.language_models import BaseChatModel

from repositories.agent_config_repository import AgentConfigRepository

logger = logging.getLogger(__name__)

DEFAULT_ROUTING_PROMPT = """ユーザーの質問を分析し、最適なエージェントを選択してください。

選択肢:
- "search": 複雑な質問、比較、要約、ドキュメント検索が必要な質問
- "chat": 雑談、挨拶、簡単な質問、一般知識の質問

質問: {query}

JSON形式で回答してください:
{{"agent": "search" or "chat", "reason": "選択理由"}}"""


def determine_agent_type(
    llm: BaseChatModel,
    query: str,
    agent_config_repo: Optional[AgentConfigRepository] = None,
) -> str:
    """Determine which agent should handle the query.

    Returns: "search" or "chat"
    """
    # Load routing rules from DB
    routing_prompt = DEFAULT_ROUTING_PROMPT
    if agent_config_repo:
        try:
            rules = agent_config_repo.list_routing_rules()
            if rules:
                routing_prompt = rules[0].condition_prompt
        except Exception as e:
            logger.warning("Failed to load routing rules: %s", e)

    formatted = routing_prompt.format(query=query)

    try:
        result = llm.invoke(formatted)
        content = result.content
        parsed = json.loads(content) if "{" in content else {"agent": "chat"}
        agent_type = parsed.get("agent", "chat")
        reason = parsed.get("reason", "")
        logger.info("Supervisor routing: query='%s' → agent='%s' (%s)", query[:50], agent_type, reason)
        return agent_type if agent_type in ("search", "chat") else "chat"
    except Exception as e:
        logger.warning("Supervisor routing failed, defaulting to chat: %s", e)
        return "chat"
