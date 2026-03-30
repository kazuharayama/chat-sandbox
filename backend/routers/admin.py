from fastapi import APIRouter, Depends, HTTPException

from core.auth import require_admin
from core.dependencies import get_agent_config_repository
from models.agent_config import (
    KnowledgeSourceUpdateRequest,
    LLMModelCreateRequest,
    LLMModelUpdateRequest,
    PromptUpdateRequest,
)
from repositories.agent_config_repository import AgentConfigRepository
from services.llm_factory import clear_llm_cache

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# --- LLM Models ---

@router.get("/models")
async def list_models(repo: AgentConfigRepository = Depends(get_agent_config_repository)):
    return repo.list_models()


@router.post("/models")
async def create_model(
    body: LLMModelCreateRequest,
    repo: AgentConfigRepository = Depends(get_agent_config_repository),
):
    model = repo.create_model(body)
    clear_llm_cache()
    return model


@router.put("/models/{model_id}")
async def update_model(
    model_id: str,
    body: LLMModelUpdateRequest,
    repo: AgentConfigRepository = Depends(get_agent_config_repository),
):
    model = repo.update_model(
        model_id,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
        is_default=body.is_default,
        config=body.config,
    )
    if not model:
        raise HTTPException(status_code=404, detail="モデルが見つかりません")
    clear_llm_cache()
    return model


# --- Agents ---

@router.get("/agents")
async def list_agents(repo: AgentConfigRepository = Depends(get_agent_config_repository)):
    return repo.list_agents()


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str, repo: AgentConfigRepository = Depends(get_agent_config_repository)):
    agent = repo.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="エージェントが見つかりません")
    return agent


# --- Prompts (specific routes BEFORE parameterized routes) ---

@router.get("/agents/{agent_id}/prompts")
async def get_prompts(agent_id: str, repo: AgentConfigRepository = Depends(get_agent_config_repository)):
    return repo.get_active_prompts(agent_id)


@router.get("/prompts/{agent_id}/{prompt_key}/versions")
async def get_prompt_versions(
    agent_id: str, prompt_key: str,
    repo: AgentConfigRepository = Depends(get_agent_config_repository),
):
    return repo.get_prompt_versions(agent_id, prompt_key)


@router.put("/prompts/{agent_id}/{prompt_key}")
async def update_prompt(
    agent_id: str, prompt_key: str, body: PromptUpdateRequest,
    repo: AgentConfigRepository = Depends(get_agent_config_repository),
):
    return repo.update_prompt(agent_id, prompt_key, body.content, body.updated_by)


@router.post("/prompts/{agent_id}/{prompt_key}/rollback/{version}")
async def rollback_prompt(
    agent_id: str, prompt_key: str, version: int,
    repo: AgentConfigRepository = Depends(get_agent_config_repository),
):
    result = repo.rollback_prompt(agent_id, prompt_key, version)
    if not result:
        raise HTTPException(status_code=404, detail="指定バージョンが見つかりません")
    return result


# --- Parameters ---

@router.get("/agents/{agent_id}/parameters")
async def get_parameters(agent_id: str, repo: AgentConfigRepository = Depends(get_agent_config_repository)):
    return repo.get_parameters(agent_id)


# --- Knowledge Sources ---

@router.get("/knowledge-sources")
async def list_knowledge_sources(repo: AgentConfigRepository = Depends(get_agent_config_repository)):
    return repo.list_knowledge_sources()


@router.put("/knowledge-sources/{source_id}")
async def update_knowledge_source(
    source_id: str,
    body: KnowledgeSourceUpdateRequest,
    repo: AgentConfigRepository = Depends(get_agent_config_repository),
):
    source = repo.update_knowledge_source(source_id, config=body.config, is_enabled=body.is_enabled)
    if not source:
        raise HTTPException(status_code=404, detail="ナレッジソースが見つかりません")
    return source


# --- Routing Rules ---

@router.get("/routing-rules")
async def list_routing_rules(repo: AgentConfigRepository = Depends(get_agent_config_repository)):
    return repo.list_routing_rules()


# --- Cache Management ---

@router.post("/cache/clear")
async def clear_cache():
    clear_llm_cache()
    return {"status": "ok", "message": "LLMキャッシュをクリアしました"}
