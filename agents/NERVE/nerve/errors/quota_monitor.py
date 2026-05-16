from nerve.db.postgres import update_provider_status, get_provider_status

# Maps agents to LLM providers (verified from source code):
#   IRIS -> Anthropic (Claude Haiku) or OpenAI (GPT-4o-mini)
#   CELL -> OpenAI (text-embedding-3-small for dedup + gpt-4o-mini for enrichment)
#   CORTEX -> Anthropic (assumed)
AGENT_PROVIDER_MAP = {
    "iris": "anthropic",    # default provider
    "cell": "openai",       # embeddings + enrichment
    "cortex": "anthropic",  # assumed
}

async def mark_provider_down(agent: str, error_type: str):
    provider = AGENT_PROVIDER_MAP.get(agent)
    if provider:
        await update_provider_status(provider, error_type)

async def should_skip_job(job_def: dict) -> bool:
    """If the job's LLM provider is down, skip it instead of wasting quota."""
    provider = AGENT_PROVIDER_MAP.get(job_def["agent"])
    if provider:
        status = await get_provider_status(provider)
        return status in ("quota_exceeded", "credits_exhausted")
    return False
