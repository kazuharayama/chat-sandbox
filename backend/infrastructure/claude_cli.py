"""
ChatClaudeCLI: LangChain BaseChatModel wrapper for `claude -p`.

Uses the Claude Code CLI (included in Claude Teams subscription)
as an LLM backend via subprocess.
"""
import asyncio
import json
import logging
import subprocess
from typing import Any, Iterator, List, Optional

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult

logger = logging.getLogger(__name__)


def _messages_to_prompt(messages: List[BaseMessage]) -> str:
    """Convert LangChain messages to a single prompt string for claude -p."""
    parts = []
    for msg in messages:
        if isinstance(msg, SystemMessage):
            parts.append(f"<system>\n{msg.content}\n</system>")
        elif isinstance(msg, HumanMessage):
            # Handle multimodal content (text + images)
            if isinstance(msg.content, list):
                text_parts = [c["text"] for c in msg.content if c.get("type") == "text"]
                parts.append(f"<user>\n{' '.join(text_parts)}\n</user>")
            else:
                parts.append(f"<user>\n{msg.content}\n</user>")
        elif isinstance(msg, AIMessage):
            parts.append(f"<assistant>\n{msg.content}\n</assistant>")
        else:
            parts.append(str(msg.content))
    return "\n\n".join(parts)


class ChatClaudeCLI(BaseChatModel):
    """LangChain chat model that calls Claude via the CLI (`claude -p`)."""

    model_name: str = "claude"
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

    @property
    def _llm_type(self) -> str:
        return "claude-cli"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt = _messages_to_prompt(messages)

        cmd = ["claude", "-p", prompt, "--output-format", "text"]
        if self.max_tokens:
            cmd.extend(["--max-turns", "1"])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                logger.error("claude -p failed: %s", result.stderr)
                content = f"Error: Claude CLI returned code {result.returncode}"
            else:
                content = result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.error("claude -p timed out")
            content = "Error: Claude CLI timed out"
        except FileNotFoundError:
            logger.error("claude command not found. Is Claude Code CLI installed?")
            content = "Error: Claude CLI not found"

        message = AIMessage(content=content)
        return ChatResult(generations=[ChatGeneration(message=message)])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt = _messages_to_prompt(messages)

        cmd = ["claude", "-p", prompt, "--output-format", "text"]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

            if proc.returncode != 0:
                logger.error("claude -p failed: %s", stderr.decode())
                content = f"Error: Claude CLI returned code {proc.returncode}"
            else:
                content = stdout.decode().strip()
        except asyncio.TimeoutError:
            logger.error("claude -p timed out")
            content = "Error: Claude CLI timed out"
        except FileNotFoundError:
            logger.error("claude command not found")
            content = "Error: Claude CLI not found"

        message = AIMessage(content=content)
        return ChatResult(generations=[ChatGeneration(message=message)])

    @property
    def _identifying_params(self) -> dict:
        return {"model_name": self.model_name}
