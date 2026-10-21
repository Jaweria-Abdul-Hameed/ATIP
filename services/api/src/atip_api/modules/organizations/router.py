"""Organization and RBAC management router."""

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from atip_api.core.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from atip_api.core.pagination import PaginationMetadata, PaginationParams, get_pagination_params
from atip_api.core.responses import DataResponse, PaginatedResponse
from atip_api.db.models.organization import (
    MembershipRole,
    Organization,
    OrganizationInvitation,
    OrganizationMembership,
    User,
)
from atip_api.db.session import get_db
from atip_api.modules.identity.deps import get_current_active_user, get_optional_current_user
from atip_api.modules.organizations.deps import OrgContext, get_org_context, require_org_role
from atip_api.modules.organizations.schemas import (
    InvitationAcceptResponse,
    InvitationCreate,
    InvitationRead,
    MembershipRead,
    MembershipUpdate,
    OrganizationCreate,
    OrganizationRead,
)

router = APIRouter(tags=["Organizations"])


@router.get("/organizations", response_model=PaginatedResponse[OrganizationRead])
async def list_organizations(
    pagination: PaginationParams = Depends(get_pagination_params),
    user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[OrganizationRead]:
    """List organizations accessible to the current user with their active role."""
    if user:
        # User is authenticated: return organizations they belong to
        stmt = (
            select(Organization, OrganizationMembership.role)
            .join(
                OrganizationMembership,
                Organization.id == OrganizationMembership.organization_id,
            )
            .where(
                OrganizationMembership.user_id == user.id,
                Organization.is_active.is_(True),
            )
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        result = await db.execute(stmt)
        rows = result.all()

        count_stmt = (
            select(func.count(Organization.id))
            .join(
                OrganizationMembership,
                Organization.id == OrganizationMembership.organization_id,
            )
            .where(
                OrganizationMembership.user_id == user.id,
                Organization.is_active.is_(True),
            )
        )
        total_items = (await db.execute(count_stmt)).scalar() or 0

        items = [
            OrganizationRead(
                id=org.id,
                slug=org.slug,
                name=org.name,
                billing_tier=org.billing_tier,
                role=role.value if hasattr(role, "value") else str(role),
                created_at=org.created_at,
                updated_at=org.updated_at,
            )
            for org, role in rows
        ]
    else:
        # Fallback for unauthenticated dev queries
        stmt = select(Organization).where(Organization.is_active.is_(True)).offset(pagination.offset).limit(pagination.limit)
        result = await db.execute(stmt)
        orgs = result.scalars().all()
        count_stmt = select(func.count(Organization.id)).where(Organization.is_active.is_(True))
        total_items = (await db.execute(count_stmt)).scalar() or 0

        items = [
            OrganizationRead(
                id=org.id,
                slug=org.slug,
                name=org.name,
                billing_tier=org.billing_tier,
                role="viewer",
                created_at=org.created_at,
                updated_at=org.updated_at,
            )
            for org in orgs
        ]

    return PaginatedResponse(
        data=items,
        pagination=PaginationMetadata.create(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total_items,
        ),
    )


@router.post(
    "/organizations",
    response_model=DataResponse[OrganizationRead],
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(
    payload: OrganizationCreate,
    user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[OrganizationRead]:
    """Create a new organization and assign creator as Owner."""
    # Check slug uniqueness
    slug_check = await db.execute(select(Organization).where(Organization.slug == payload.slug))
    if slug_check.scalar_one_or_none():
        raise ConflictError(message=f"Organization slug '{payload.slug}' is already taken.")

    org = Organization(
        name=payload.name,
        slug=payload.slug,
        billing_tier=payload.billing_tier,
        is_active=True,
    )
    db.add(org)
    await db.flush()

    # If authenticated, assign user as Owner
    user_role = "owner"
    if user:
        membership = OrganizationMembership(
            organization_id=org.id,
            user_id=user.id,
            role=MembershipRole.OWNER,
        )
        db.add(membership)

    await db.commit()

    return DataResponse(
        data=OrganizationRead(
            id=org.id,
            slug=org.slug,
            name=org.name,
            billing_tier=org.billing_tier,
            role=user_role,
            created_at=org.created_at,
            updated_at=org.updated_at,
        )
    )


@router.get("/organizations/{id}", response_model=DataResponse[OrganizationRead])
async def get_organization(
    id: str,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
) -> DataResponse[OrganizationRead]:
    """Get organization by ID or slug."""
    stmt = (
        select(Organization)
        .options(selectinload(Organization.memberships))
        .where(
            (Organization.id == id) | (Organization.slug == id),
            Organization.is_active.is_(True),
        )
    )
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()
    if not org:
        raise NotFoundError(message=f"Organization '{id}' not found")

    user_role = "viewer"
    if user:
        user_m = next((m for m in org.memberships if m.user_id == user.id), None)
        if user_m:
            user_role = user_m.role.value if hasattr(user_m.role, "value") else str(user_m.role)

    return DataResponse(
        data=OrganizationRead(
            id=org.id,
            slug=org.slug,
            name=org.name,
            billing_tier=org.billing_tier,
            role=user_role,
            created_at=org.created_at,
            updated_at=org.updated_at,
        )
    )


# ---------------------------------------------------------------------------
# Membership Management & RBAC: /organizations/{org_id}/members
# ---------------------------------------------------------------------------

@router.get(
    "/organizations/{org_id}/members",
    response_model=DataResponse[list[MembershipRead]],
)
async def list_organization_members(
    context: OrgContext = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[list[MembershipRead]]:
    """List all members and roles in the organization."""
    stmt = (
        select(OrganizationMembership)
        .options(selectinload(OrganizationMembership.user))
        .where(OrganizationMembership.organization_id == context.organization.id)
    )
    result = await db.execute(stmt)
    memberships = result.scalars().all()

    items = [
        MembershipRead(
            id=m.id,
            user_id=m.user_id,
            email=m.user.email if m.user else "unknown",
            name=m.user.name if m.user else "Unknown Member",
            avatar_url=m.user.avatar_url if m.user else None,
            role=m.role.value if hasattr(m.role, "value") else str(m.role),
            created_at=m.created_at,
        )
        for m in memberships
    ]
    return DataResponse(data=items)


@router.patch(
    "/organizations/{org_id}/members/{user_id}",
    response_model=DataResponse[MembershipRead],
)
async def update_member_role(
    user_id: str,
    payload: MembershipUpdate,
    context: OrgContext = Depends(require_org_role(MembershipRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[MembershipRead]:
    """Update a member's role (requires Admin or Owner)."""
    # Find targeted membership
    stmt = (
        select(OrganizationMembership)
        .options(selectinload(OrganizationMembership.user))
        .where(
            OrganizationMembership.organization_id == context.organization.id,
            OrganizationMembership.user_id == user_id,
        )
    )
    result = await db.execute(stmt)
    target_membership = result.scalar_one_or_none()

    if not target_membership:
        raise NotFoundError(message=f"User '{user_id}' is not a member of this organization.")

    # Only an Owner can change an Owner's role or promote someone to Owner
    if target_membership.role == MembershipRole.OWNER and context.role != MembershipRole.OWNER:
        raise ForbiddenError(message="Only an Owner can modify an Owner's membership role.")

    if payload.role == MembershipRole.OWNER and context.role != MembershipRole.OWNER:
        raise ForbiddenError(message="Only an Owner can grant Owner privileges.")

    # Prevent demoting the last remaining Owner
    if target_membership.role == MembershipRole.OWNER and payload.role != MembershipRole.OWNER:
        owner_count_stmt = select(func.count(OrganizationMembership.id)).where(
            OrganizationMembership.organization_id == context.organization.id,
            OrganizationMembership.role == MembershipRole.OWNER,
        )
        owner_count = (await db.execute(owner_count_stmt)).scalar() or 0
        if owner_count <= 1:
            raise ValidationError(
                message="Cannot demote the last remaining Owner of the organization."
            )

    target_membership.role = payload.role
    await db.commit()

    return DataResponse(
        data=MembershipRead(
            id=target_membership.id,
            user_id=target_membership.user_id,
            email=target_membership.user.email,
            name=target_membership.user.name,
            avatar_url=target_membership.user.avatar_url,
            role=target_membership.role.value,
            created_at=target_membership.created_at,
        )
    )


@router.delete(
    "/organizations/{org_id}/members/{user_id}",
    response_model=DataResponse[dict[str, str]],
)
async def remove_member(
    user_id: str,
    context: OrgContext = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[dict[str, str]]:
    """Remove a member from the organization (or self-leave)."""
    is_self = context.user.id == user_id
    is_admin_or_owner = context.role in (MembershipRole.ADMIN, MembershipRole.OWNER)

    if not is_self and not is_admin_or_owner:
        raise ForbiddenError(message="Insufficient permissions to remove organization members.")

    stmt = select(OrganizationMembership).where(
        OrganizationMembership.organization_id == context.organization.id,
        OrganizationMembership.user_id == user_id,
    )
    result = await db.execute(stmt)
    target_membership = result.scalar_one_or_none()

    if not target_membership:
        raise NotFoundError(message=f"Member '{user_id}' not found in this organization.")

    # Protect last remaining owner from leaving / being deleted
    if target_membership.role == MembershipRole.OWNER:
        owner_count_stmt = select(func.count(OrganizationMembership.id)).where(
            OrganizationMembership.organization_id == context.organization.id,
            OrganizationMembership.role == MembershipRole.OWNER,
        )
        owner_count = (await db.execute(owner_count_stmt)).scalar() or 0
        if owner_count <= 1:
            raise ValidationError(
                message="Cannot remove the last remaining Owner. Transfer ownership before leaving."
            )

    await db.delete(target_membership)
    await db.commit()

    return DataResponse(
        data={"message": f"Member '{user_id}' removed from organization '{context.organization.slug}'."}
    )


# ---------------------------------------------------------------------------
# Organization Invitations: /organizations/{org_id}/invitations
# ---------------------------------------------------------------------------

def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


@router.get(
    "/organizations/{org_id}/invitations",
    response_model=DataResponse[list[InvitationRead]],
)
async def list_pending_invitations(
    context: OrgContext = Depends(require_org_role(MembershipRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[list[InvitationRead]]:
    """List pending invitations for the organization."""
    now = datetime.now(UTC)
    stmt = (
        select(OrganizationInvitation)
        .where(
            OrganizationInvitation.organization_id == context.organization.id,
            OrganizationInvitation.accepted_at.is_(None),
        )
        .order_by(OrganizationInvitation.created_at.desc())
    )
    result = await db.execute(stmt)
    invitations = [inv for inv in result.scalars().all() if _ensure_utc(inv.expires_at) > now]

    items = [
        InvitationRead(
            id=inv.id,
            organization_id=inv.organization_id,
            email=inv.email,
            role=inv.role.value if hasattr(inv.role, "value") else str(inv.role),
            invited_by_user_id=inv.invited_by_user_id,
            token=inv.token,
            expires_at=inv.expires_at,
            created_at=inv.created_at,
        )
        for inv in invitations
    ]
    return DataResponse(data=items)


@router.post(
    "/organizations/{org_id}/invitations",
    response_model=DataResponse[InvitationRead],
    status_code=status.HTTP_201_CREATED,
)
async def invite_member(
    payload: InvitationCreate,
    context: OrgContext = Depends(require_org_role(MembershipRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[InvitationRead]:
    """Invite a new member to the organization by email."""
    # Check if target email already belongs to a member
    member_check = (
        select(OrganizationMembership)
        .join(User, OrganizationMembership.user_id == User.id)
        .where(
            OrganizationMembership.organization_id == context.organization.id,
            User.email == payload.email,
        )
    )
    if (await db.execute(member_check)).scalar_one_or_none():
        raise ConflictError(message=f"User with email '{payload.email}' is already a member.")

    token = f"inv_tok_{secrets.token_urlsafe(32)}"
    expires_at = datetime.now(UTC) + timedelta(days=7)

    invitation = OrganizationInvitation(
        organization_id=context.organization.id,
        email=payload.email,
        role=payload.role,
        invited_by_user_id=context.user.id,
        token=token,
        expires_at=expires_at,
    )
    db.add(invitation)
    await db.commit()

    return DataResponse(
        data=InvitationRead(
            id=invitation.id,
            organization_id=invitation.organization_id,
            email=invitation.email,
            role=invitation.role.value if hasattr(invitation.role, "value") else str(invitation.role),
            invited_by_user_id=invitation.invited_by_user_id,
            token=invitation.token,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
        )
    )


@router.post(
    "/invitations/{token}/accept",
    response_model=DataResponse[InvitationAcceptResponse],
)
async def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[InvitationAcceptResponse]:
    """Accept an organization invitation and join as member."""
    stmt = (
        select(OrganizationInvitation)
        .options(selectinload(OrganizationInvitation.organization))
        .where(OrganizationInvitation.token == token)
    )
    result = await db.execute(stmt)
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise NotFoundError(message="Invitation token is invalid or does not exist.")

    if invitation.accepted_at is not None:
        raise ConflictError(message="This invitation has already been accepted.")

    now = datetime.now(UTC)
    if _ensure_utc(invitation.expires_at) < now:
        raise ValidationError(message="This invitation has expired.")

    # Check if already a member
    existing_membership = await db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == invitation.organization_id,
            OrganizationMembership.user_id == current_user.id,
        )
    )
    if not existing_membership.scalar_one_or_none():
        membership = OrganizationMembership(
            organization_id=invitation.organization_id,
            user_id=current_user.id,
            role=invitation.role,
        )
        db.add(membership)

    invitation.accepted_at = now
    await db.commit()

    return DataResponse(
        data=InvitationAcceptResponse(
            success=True,
            organization_id=invitation.organization.id,
            organization_name=invitation.organization.name,
            role=invitation.role.value if hasattr(invitation.role, "value") else str(invitation.role),
            message=f"Successfully joined organization '{invitation.organization.name}'.",
        )
    )
