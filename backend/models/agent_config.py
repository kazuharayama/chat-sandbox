from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class LLMModelInfo(BaseModel):
    id: str
    name: str
    provider: str  # ollama, openai_compatible
    deployment_name: str
    temperature: Optional[float]
    max_tokens: Optional[int]
    is_default: bool
    config: Any  # provider-specific config (JSONB)


class LLMModelCreateRequest(BaseModel):
    name: str
    provider: str  # ollama, openai_compatible
    deployment_name: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    is_default: bool = False
    config: Optional[dict] = None


class LLMModelUpdateRequest(BaseModel):
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    is_default: Optional[bool] = None
    config: Optional[dict] = None


class KnowledgeSourceUpdateRequest(BaseModel):
    config: Optional[dict] = None
    is_enabled: Optional[bool] = None


class AgentInfo(BaseModel):
    id: str
    name: str
    display_name: str
    description: Optional[str]
    agent_type: str
    llm_model_id: Optional[str]
    is_enabled: bool
    sort_order: int


class PromptInfo(BaseModel):
    id: str
    agent_id: str
    prompt_key: str
    content: str
    version: int
    is_active: bool
    updated_by: Optional[str]
    created_at: datetime


class PromptUpdateRequest(BaseModel):
    content: str
    updated_by: Optional[str] = None


class AgentParameterInfo(BaseModel):
    id: str
    agent_id: str
    param_key: str
    param_value: str
    param_type: str
    description: Optional[str]


class RoutingRuleInfo(BaseModel):
    id: str
    name: str
    description: Optional[str]
    source_agent_id: str
    condition_prompt: str
    routes: Any
    is_enabled: bool


class KnowledgeSourceInfo(BaseModel):
    id: str
    name: str
    source_type: str
    collection_name: str
    config: Any
    is_enabled: bool
