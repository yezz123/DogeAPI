"""API keys router.

All endpoints require a JWT (UI is the canonical caller); the X-API-Key
itself is for machine clients hitting domain endpoints elsewhere.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from authx import TokenPayload
from fastapi import APIRouter, Depends, HTTPException, Response, status

from dogeapi.api_keys import service
from dogeapi.api_keys.schemas import (
    APIKeyCreate,
    APIKeyCreatedResponse,
    APIKeyResponse,
)
from dogeapi.deps import SessionDep, UserDep
from dogeapi.security import OrgMatch, require_scope

router = APIRouter(tags=["api-keys"])


@router.post(
    "/orgs/{slug}/api-keys",
    response_model=APIKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_org_api_key(
    body: APIKeyCreate,
    org: OrgMatch,
    session: SessionDep,
    user: UserDep,
    payload: Annotated[TokenPayload, Depends(require_scope("org:apikeys:write"))],
) -> APIKeyCreatedResponse:
    """Create a new API key. Returned plaintext is shown only once."""
    try:
        key, plaintext = await service.create_api_key(
            session,
            org_id=org.id,
            creator=user,
            name=body.name,
            requested_scopes=body.scopes,
            creator_scopes=list(payload.scopes or []),
            expires_at=body.expires_at,
        )
    except service.ScopeNotPermittedError as exc:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "You cannot grant scopes you don't hold",
        ) from exc

    return APIKeyCreatedResponse(
        api_key=APIKeyResponse.model_validate(key),
        plaintext_key=plaintext,
    )


@router.get(
    "/orgs/{slug}/api-keys",
    response_model=list[APIKeyResponse],
    dependencies=[Depends(require_scope("org:apikeys:read"))],
)
async def list_org_api_keys(
    org: OrgMatch,
    session: SessionDep,
) -> list[APIKeyResponse]:
    rows = await service.list_api_keys(session, org.id)
    return [APIKeyResponse.model_validate(k) for k in rows]


@router.delete(
    "/orgs/{slug}/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_scope("org:apikeys:write"))],
)
async def revoke_org_api_key(
    key_id: UUID,
    org: OrgMatch,
    session: SessionDep,
) -> Response:
    try:
        await service.revoke_api_key(session, org_id=org.id, key_id=key_id)
    except service.APIKeyNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "API key not found") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
