"""AI service: thread/message CRUD + agent orchestration."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from dogeapi.models import AIMessage, AIThread, User

if TYPE_CHECKING:
    from dogeapi.ai.agent import AgentResponse


class ThreadNotFoundError(Exception):
    pass


class QuotaExceededError(Exception):
    pass


async def list_threads(session: AsyncSession, org_id: UUID, user_id: UUID) -> list[AIThread]:
    stmt = (
        select(AIThread)
        .where(AIThread.org_id == org_id, AIThread.user_id == user_id)
        .order_by(desc(AIThread.updated_at))
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_thread(session: AsyncSession, *, org_id: UUID, thread_id: UUID, user_id: UUID) -> AIThread:
    thread = await session.get(AIThread, thread_id)
    if thread is None or thread.org_id != org_id or thread.user_id != user_id:
        raise ThreadNotFoundError(str(thread_id))
    return thread


async def list_messages(session: AsyncSession, thread_id: UUID) -> list[AIMessage]:
    stmt = select(AIMessage).where(AIMessage.thread_id == thread_id).order_by(AIMessage.created_at)
    return list((await session.execute(stmt)).scalars().all())


async def create_thread(
    session: AsyncSession,
    *,
    org_id: UUID,
    user: User,
    title: str | None = None,
) -> AIThread:
    thread = AIThread(
        org_id=org_id,
        user_id=user.id,
        title=title or "New conversation",
    )
    session.add(thread)
    await session.flush()
    return thread


async def delete_thread(session: AsyncSession, *, org_id: UUID, thread_id: UUID, user_id: UUID) -> None:
    thread = await get_thread(session, org_id=org_id, thread_id=thread_id, user_id=user_id)
    await session.delete(thread)
    await session.flush()


async def append_user_message(session: AsyncSession, *, thread: AIThread, content: str) -> AIMessage:
    msg = AIMessage(thread_id=thread.id, role="user", content=content)
    session.add(msg)
    await session.flush()
    return msg


async def append_assistant_message(
    session: AsyncSession,
    *,
    thread: AIThread,
    response: AgentResponse,
) -> AIMessage:
    msg = AIMessage(
        thread_id=thread.id,
        role="assistant",
        content=response.text,
        tokens_in=response.tokens_in,
        tokens_out=response.tokens_out,
        model=response.model,
    )
    session.add(msg)
    await session.flush()
    return msg
