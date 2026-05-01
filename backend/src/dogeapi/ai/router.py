"""AI chat router: threads + messages + quota + model discovery + agents demo."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from dogeapi.ai import gateway, quota, service
from dogeapi.ai.agent import get_agent
from dogeapi.ai.schemas import (
    MessageRequest,
    MessageResponse,
    ModelInfo,
    ModelsListResponse,
    SendMessageResponse,
    ThreadCreate,
    ThreadDetailResponse,
    ThreadResponse,
)
from dogeapi.billing.limits import get_plan_limits
from dogeapi.deps import RedisDep, SessionDep, SettingsDep, UserDep
from dogeapi.security import OrgMatch, require_scope

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orgs/{slug}/ai", tags=["ai"])

DEFAULT_RESERVE = 4_000


# ─── Models discovery ─────────────────────────────────────────────────────


@router.get(
    "/models",
    response_model=ModelsListResponse,
    dependencies=[Depends(require_scope("org:ai:use"))],
)
async def list_org_ai_models(
    org: OrgMatch,
    settings: SettingsDep,
) -> ModelsListResponse:
    """List models the configured LLM Gateway exposes.

    When no API key is configured, returns a single ``echo`` placeholder so
    the frontend stays renderable in offline / dev mode.
    """
    configured = bool(settings.LLM_GATEWAY_API_KEY)
    if not configured:
        return ModelsListResponse(
            configured=False,
            default_model="echo",
            models=[
                ModelInfo(
                    id="echo",
                    name="Offline Echo",
                    family="local",
                    description=("Deterministic offline agent (no LLM gateway key configured)."),
                    context_length=4096,
                    input_modalities=["text"],
                    output_modalities=["text"],
                    json_output=False,
                    structured_outputs=False,
                    free=True,
                    deprecated=False,
                )
            ],
        )

    try:
        models = await gateway.list_models(settings)
    except gateway.LLMGatewayError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"Could not reach LLM gateway: {exc.detail}",
        ) from exc

    return ModelsListResponse(
        configured=True,
        default_model=settings.AI_DEFAULT_MODEL,
        models=[
            ModelInfo(
                id=m.id,
                name=m.name,
                family=m.family,
                description=m.description,
                context_length=m.context_length,
                input_modalities=m.input_modalities,
                output_modalities=m.output_modalities,
                json_output=m.json_output,
                structured_outputs=m.structured_outputs,
                free=m.free,
                deprecated=m.deprecated,
            )
            for m in models
            if not m.deprecated
        ],
    )


# ─── Threads ──────────────────────────────────────────────────────────────


@router.get(
    "/threads",
    response_model=list[ThreadResponse],
    dependencies=[Depends(require_scope("org:ai:use"))],
)
async def list_org_threads(org: OrgMatch, session: SessionDep, user: UserDep) -> list[ThreadResponse]:
    threads = await service.list_threads(session, org.id, user.id)
    return [ThreadResponse.model_validate(t) for t in threads]


@router.post(
    "/threads",
    response_model=ThreadResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scope("org:ai:use"))],
)
async def create_org_thread(
    body: ThreadCreate,
    org: OrgMatch,
    session: SessionDep,
    user: UserDep,
) -> ThreadResponse:
    thread = await service.create_thread(
        session,
        org_id=org.id,
        user=user,
        title=body.title,
        default_model=body.default_model,
    )
    return ThreadResponse.model_validate(thread)


@router.get(
    "/threads/{thread_id}",
    response_model=ThreadDetailResponse,
    dependencies=[Depends(require_scope("org:ai:use"))],
)
async def get_org_thread(
    thread_id: UUID,
    org: OrgMatch,
    session: SessionDep,
    user: UserDep,
) -> ThreadDetailResponse:
    try:
        thread = await service.get_thread(session, org_id=org.id, thread_id=thread_id, user_id=user.id)
    except service.ThreadNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Thread not found") from exc
    messages = await service.list_messages(session, thread.id)
    return ThreadDetailResponse(
        thread=ThreadResponse.model_validate(thread),
        messages=[MessageResponse.model_validate(m) for m in messages],
    )


@router.delete(
    "/threads/{thread_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_scope("org:ai:use"))],
)
async def delete_org_thread(
    thread_id: UUID,
    org: OrgMatch,
    session: SessionDep,
    user: UserDep,
) -> Response:
    try:
        await service.delete_thread(session, org_id=org.id, thread_id=thread_id, user_id=user.id)
    except service.ThreadNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Thread not found") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ─── Messages ─────────────────────────────────────────────────────────────


@router.post(
    "/threads/{thread_id}/messages",
    response_model=SendMessageResponse,
    dependencies=[Depends(require_scope("org:ai:use"))],
)
async def send_message(
    thread_id: UUID,
    body: MessageRequest,
    org: OrgMatch,
    session: SessionDep,
    user: UserDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> SendMessageResponse:
    try:
        thread = await service.get_thread(session, org_id=org.id, thread_id=thread_id, user_id=user.id)
    except service.ThreadNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Thread not found") from exc

    plan_limit = get_plan_limits(org.plan).monthly_ai_tokens
    reserved = await quota.check_and_reserve(redis, org.id, estimate=DEFAULT_RESERVE, limit=plan_limit)
    if not reserved:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Monthly AI token quota exceeded",
        )

    user_message = await service.append_user_message(session, thread=thread, content=body.content)

    history_rows = await service.list_messages(session, thread.id)
    history = [{"role": m.role, "content": m.content} for m in history_rows]

    chosen_model = body.model or thread.default_model or settings.AI_DEFAULT_MODEL

    agent = get_agent(settings)
    try:
        agent_response = await agent.respond(history, model=chosen_model)
    except gateway.LLMGatewayError as exc:
        await quota.refund(redis, org.id, delta=-DEFAULT_RESERVE)
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"LLM gateway error ({exc.status}): {exc.detail}",
        ) from exc
    except Exception as exc:  # pragma: no cover - upstream failures
        await quota.refund(redis, org.id, delta=-DEFAULT_RESERVE)
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"LLM call failed: {exc}",
        ) from exc

    actual_total = agent_response.tokens_in + agent_response.tokens_out
    await quota.refund(redis, org.id, delta=actual_total - DEFAULT_RESERVE)

    if thread.default_model is None and body.model:
        thread.default_model = body.model
        await session.flush()

    assistant_message = await service.append_assistant_message(session, thread=thread, response=agent_response)

    monthly_used = await quota.monthly_usage(redis, org.id)

    return SendMessageResponse(
        user_message=MessageResponse.model_validate(user_message),
        assistant_message=MessageResponse.model_validate(assistant_message),
        monthly_tokens_used=monthly_used,
        monthly_token_limit=plan_limit,
    )


# ─── Pydantic AI agent demos ─────────────────────────────────────────────
#
# These wrap the example agents in :mod:`dogeapi.ai.examples` as HTTP
# endpoints. They exist so the frontend has something concrete to render
# against; replace them with your own agents in production.


def _require_gateway(settings: SettingsDep) -> None:
    if not settings.LLM_GATEWAY_API_KEY:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "LLM_GATEWAY_API_KEY not configured",
        )


class AgentTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)


class AgentTextResponse(BaseModel):
    text: str
    model: str | None = None


@router.get(
    "/agents",
    dependencies=[Depends(require_scope("org:ai:use"))],
)
async def list_demo_agents(org: OrgMatch) -> dict[str, list[dict[str, str]]]:
    """Static catalogue of demo agents the frontend can render."""
    return {
        "agents": [
            {
                "id": "task-extractor",
                "name": "Task extractor",
                "description": (
                    "Pulls a single actionable task (title, deadline, "
                    "priority) out of free-form text using a structured "
                    "Pydantic AI output."
                ),
                "input_label": "Describe what needs to happen…",
                "output_kind": "json",
            },
            {
                "id": "concierge",
                "name": "Concierge (with tool)",
                "description": (
                    "Answers using a small Python tool that returns today's "
                    "date — demonstrates Pydantic AI tool-calling through "
                    "the gateway."
                ),
                "input_label": "Ask the concierge…",
                "output_kind": "text",
            },
        ]
    }


@router.post(
    "/agents/task-extractor",
    dependencies=[Depends(require_scope("org:ai:use"))],
)
async def run_task_extractor(
    body: AgentTextRequest,
    org: OrgMatch,
    settings: SettingsDep,
) -> dict[str, object]:
    """Run the structured-output task extractor."""
    _require_gateway(settings)

    from dogeapi.ai.examples import build_task_extractor

    agent = build_task_extractor(settings)
    try:
        result = await agent.run(body.text)
    except gateway.LLMGatewayError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Agent failed: {exc}") from exc

    usage = result.usage()
    return {
        "task": result.output.model_dump(mode="json"),
        "tokens_in": int(usage.input_tokens or 0),
        "tokens_out": int(usage.output_tokens or 0),
    }


@router.post(
    "/agents/concierge",
    response_model=AgentTextResponse,
    dependencies=[Depends(require_scope("org:ai:use"))],
)
async def run_concierge_agent(
    body: AgentTextRequest,
    org: OrgMatch,
    settings: SettingsDep,
) -> AgentTextResponse:
    """Run the tool-using concierge agent."""
    _require_gateway(settings)

    from dogeapi.ai.examples import WeatherSummary, build_concierge_agent

    agent = build_concierge_agent(settings)
    try:
        result = await agent.run(body.text, deps=WeatherSummary())
    except gateway.LLMGatewayError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Agent failed: {exc}") from exc

    return AgentTextResponse(text=str(result.output), model=settings.AI_DEFAULT_MODEL)
