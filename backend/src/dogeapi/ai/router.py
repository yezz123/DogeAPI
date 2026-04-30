"""AI chat router: threads + messages + quota."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from dogeapi.ai import quota, service
from dogeapi.ai.agent import get_agent
from dogeapi.ai.schemas import (
    MessageRequest,
    MessageResponse,
    SendMessageResponse,
    ThreadCreate,
    ThreadDetailResponse,
    ThreadResponse,
)
from dogeapi.billing.limits import get_plan_limits
from dogeapi.deps import RedisDep, SessionDep, SettingsDep, UserDep
from dogeapi.security import OrgMatch, require_scope

router = APIRouter(prefix="/orgs/{slug}/ai", tags=["ai"])

DEFAULT_RESERVE = 4_000


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
    thread = await service.create_thread(session, org_id=org.id, user=user, title=body.title)
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

    agent = get_agent(settings)
    try:
        agent_response = await agent.respond(history)
    except Exception as exc:  # pragma: no cover - upstream errors
        await quota.refund(redis, org.id, delta=-DEFAULT_RESERVE)
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"LLM call failed: {exc}",
        ) from exc

    actual_total = agent_response.tokens_in + agent_response.tokens_out
    await quota.refund(redis, org.id, delta=actual_total - DEFAULT_RESERVE)

    assistant_message = await service.append_assistant_message(session, thread=thread, response=agent_response)

    monthly_used = await quota.monthly_usage(redis, org.id)

    return SendMessageResponse(
        user_message=MessageResponse.model_validate(user_message),
        assistant_message=MessageResponse.model_validate(assistant_message),
        monthly_tokens_used=monthly_used,
        monthly_token_limit=plan_limit,
    )
