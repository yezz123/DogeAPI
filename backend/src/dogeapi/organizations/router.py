"""Organizations router: orgs, members, invitations, switch-org, leave.

Authorization model:

- Routes that operate *outside* an org (create, list mine, switch, accept
  invite) just require an authenticated user.
- Routes that operate *inside* an org use two layers:
    1. ``require_org_match`` &mdash; URL slug must match the JWT's ``org_id``
    2. ``require_scope("...")`` &mdash; JWT scopes must include the action's scope
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status

from dogeapi.deps import AuthDep, SessionDep, SettingsDep, UserDep
from dogeapi.models import Organization, Role, User
from dogeapi.organizations import service
from dogeapi.organizations.permissions import scopes_for_role
from dogeapi.organizations.schemas import (
    AcceptInviteRequest,
    InvitationCreatedResponse,
    InvitationResponse,
    InviteCreate,
    MembershipResponse,
    MemberSummary,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
    OrgWithRoleResponse,
    RoleChangeRequest,
    TokenPairResponse,
)
from dogeapi.security import OrgMatch, require_scope

router = APIRouter(tags=["organizations"])


# ─── Helpers ──────────────────────────────────────────────────────────────


async def _require_member(session: SessionDep, org: Organization, user: User) -> Role:
    membership = await service.get_membership(session, user_id=user.id, org_id=org.id)
    if membership is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a member of this organization")
    return membership.role


def _token_pair_with_org(auth: AuthDep, *, user_id: str, org_id: UUID, role: Role) -> TokenPairResponse:
    pair = auth.create_token_pair(
        uid=user_id,
        fresh=False,
        data={"org_id": str(org_id), "role": role.value},
        access_scopes=scopes_for_role(role),
        refresh_scopes=scopes_for_role(role),
    )
    return TokenPairResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
    )


# ─── Organizations ────────────────────────────────────────────────────────


@router.post(
    "/orgs",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_org(
    body: OrganizationCreate,
    session: SessionDep,
    user: UserDep,
) -> OrganizationResponse:
    """Create a new organization with the caller as OWNER."""
    try:
        org, _membership = await service.create_organization(session, owner=user, name=body.name, slug=body.slug)
    except service.SlugTakenError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Slug already taken") from exc
    return OrganizationResponse.model_validate(org)


@router.get("/orgs", response_model=list[OrgWithRoleResponse])
async def list_my_orgs(session: SessionDep, user: UserDep) -> list[OrgWithRoleResponse]:
    rows = await service.list_user_organizations(session, user.id)
    return [
        OrgWithRoleResponse(
            id=org.id,
            slug=org.slug,
            name=org.name,
            plan=org.plan,
            created_at=org.created_at,
            role=role,
        )
        for org, role in rows
    ]


@router.post("/orgs/{slug}/switch", response_model=TokenPairResponse)
async def switch_org(
    slug: Annotated[str, Path(min_length=2)],
    response: Response,
    session: SessionDep,
    user: UserDep,
    auth: AuthDep,
) -> TokenPairResponse:
    """Re-issue the token pair scoped to the requested org.

    Membership is verified at the DB level; no JWT scope is required because
    the caller may not yet have an active org context.
    """
    org = await service.get_organization_by_slug(session, slug)
    if org is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organization not found")
    role = await _require_member(session, org, user)

    pair = _token_pair_with_org(auth, user_id=str(user.id), org_id=org.id, role=role)
    auth.set_access_cookies(pair.access_token, response)
    auth.set_refresh_cookies(pair.refresh_token, response)
    return pair


@router.get(
    "/orgs/{slug}",
    response_model=OrganizationResponse,
    dependencies=[Depends(require_scope("org:read"))],
)
async def get_org(org: OrgMatch) -> OrganizationResponse:
    return OrganizationResponse.model_validate(org)


@router.get(
    "/orgs/{slug}/me",
    response_model=OrgWithRoleResponse,
    dependencies=[Depends(require_scope("org:read"))],
)
async def get_my_role_in_org(org: OrgMatch, session: SessionDep, user: UserDep) -> OrgWithRoleResponse:
    """Return the org plus the caller's role (used by frontend to gate UI)."""
    membership = await service.get_membership(session, user_id=user.id, org_id=org.id)
    if membership is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a member of this organization")
    return OrgWithRoleResponse(
        id=org.id,
        slug=org.slug,
        name=org.name,
        plan=org.plan,
        created_at=org.created_at,
        role=membership.role,
    )


@router.patch(
    "/orgs/{slug}",
    response_model=OrganizationResponse,
    dependencies=[Depends(require_scope("org:write"))],
)
async def update_org(
    body: OrganizationUpdate,
    org: OrgMatch,
    session: SessionDep,
) -> OrganizationResponse:
    if body.name is not None:
        org.name = body.name
    await session.flush()
    return OrganizationResponse.model_validate(org)


# ─── Members ──────────────────────────────────────────────────────────────


@router.get(
    "/orgs/{slug}/members",
    response_model=list[MemberSummary],
    dependencies=[Depends(require_scope("org:members:read"))],
)
async def list_org_members(
    org: OrgMatch,
    session: SessionDep,
) -> list[MemberSummary]:
    rows = await service.list_members(session, org.id)
    return [
        MemberSummary(
            user_id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=m.role,
            created_at=m.created_at,
        )
        for u, m in rows
    ]


@router.patch(
    "/orgs/{slug}/members/{user_id}",
    response_model=MembershipResponse,
    dependencies=[Depends(require_scope("org:members:write"))],
)
async def change_member_role(
    user_id: UUID,
    body: RoleChangeRequest,
    org: OrgMatch,
    session: SessionDep,
) -> MembershipResponse:
    try:
        membership = await service.change_role(session, org_id=org.id, target_user_id=user_id, new_role=body.role)
    except service.NotAMemberError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found") from exc
    except service.CannotRemoveLastOwnerError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Cannot demote the last owner",
        ) from exc

    return MembershipResponse.model_validate(membership)


@router.delete(
    "/orgs/{slug}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_scope("org:members:write"))],
)
async def remove_org_member(
    user_id: UUID,
    org: OrgMatch,
    session: SessionDep,
) -> Response:
    try:
        await service.remove_member(session, org_id=org.id, target_user_id=user_id)
    except service.NotAMemberError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found") from exc
    except service.CannotRemoveLastOwnerError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Cannot remove the last owner",
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/orgs/{slug}/leave",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def leave_org(
    slug: Annotated[str, Path(min_length=2)],
    session: SessionDep,
    user: UserDep,
) -> Response:
    """Self-removal endpoint &mdash; doesn't need ``org:members:write``."""
    org = await service.get_organization_by_slug(session, slug)
    if org is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organization not found")
    try:
        await service.remove_member(session, org_id=org.id, target_user_id=user.id)
    except service.NotAMemberError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not a member") from exc
    except service.CannotRemoveLastOwnerError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Promote another owner before leaving",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ─── Invitations ──────────────────────────────────────────────────────────


@router.post(
    "/orgs/{slug}/invitations",
    response_model=InvitationCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scope("org:invitations:write"))],
)
async def create_org_invitation(
    body: InviteCreate,
    org: OrgMatch,
    session: SessionDep,
    settings: SettingsDep,
    user: UserDep,
) -> InvitationCreatedResponse:
    invitation, plain_token = await service.create_invitation(
        session, org=org, email=body.email, role=body.role, invited_by=user
    )

    invite_link = f"{settings.FRONTEND_BASE_URL}/accept-invite?token={plain_token}"

    payload_link: str | None = None
    if not settings.FEATURE_EMAIL_DELIVERY:
        payload_link = invite_link
    else:
        from dogeapi.email import send_invitation_email

        await send_invitation_email(settings, to=body.email, org_name=org.name, link=invite_link)

    return InvitationCreatedResponse(
        invitation=InvitationResponse.model_validate(invitation),
        invite_link=payload_link,
    )


@router.get(
    "/orgs/{slug}/invitations",
    response_model=list[InvitationResponse],
    dependencies=[Depends(require_scope("org:invitations:read"))],
)
async def list_org_invitations(
    org: OrgMatch,
    session: SessionDep,
) -> list[InvitationResponse]:
    invitations = await service.list_invitations(session, org.id)
    return [InvitationResponse.model_validate(inv) for inv in invitations]


@router.delete(
    "/orgs/{slug}/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_scope("org:invitations:write"))],
)
async def revoke_org_invitation(
    invitation_id: UUID,
    org: OrgMatch,
    session: SessionDep,
) -> Response:
    try:
        await service.revoke_invitation(session, org_id=org.id, invitation_id=invitation_id)
    except service.InvitationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invitation not found") from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/invitations/accept",
    response_model=OrgWithRoleResponse,
)
async def accept_org_invitation(
    body: AcceptInviteRequest,
    session: SessionDep,
    user: UserDep,
) -> OrgWithRoleResponse:
    """Consume an invite token, creating a membership for the caller."""
    try:
        membership = await service.accept_invitation(session, token=body.token, user=user)
    except service.AlreadyMemberError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "You are already a member") from exc
    except service.InvitationNotFoundError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Invalid or expired invitation",
        ) from exc

    org = await session.get(Organization, membership.org_id)
    assert org is not None
    return OrgWithRoleResponse(
        id=org.id,
        slug=org.slug,
        name=org.name,
        plan=org.plan,
        created_at=org.created_at,
        role=membership.role,
    )
