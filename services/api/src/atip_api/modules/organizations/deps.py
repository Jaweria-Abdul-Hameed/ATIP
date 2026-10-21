"""Organization and RBAC dependencies for FastAPI endpoints."""

from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from atip_api.core.errors import ForbiddenError, NotFoundError, TenantMismatchError
from atip_api.db.models.organization import (
    MembershipRole,
    Organization,
    OrganizationMembership,
    User,
    has_sufficient_role,
)
from atip_api.db.session import get_db
from atip_api.modules.identity.deps import get_current_active_user


@dataclass
class OrgContext:
    organization: Organization
    membership: OrganizationMembership
    role: MembershipRole
    user: User


async def get_org_context(
    request: Request,
    x_organization_id: str | None = Header(default=None, alias="X-Organization-ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> OrgContext:
    """Resolve target organization from path parameter, header, or user's active membership,

    and verify that the user is a valid member.
    """
    path_org = request.path_params.get("org_id")
    if not path_org and "/organizations/" in request.url.path:
        path_org = request.path_params.get("id")
    target_org_id = path_org or x_organization_id

    # If neither path nor header specifies org, select first available org
    if not target_org_id:
        if current_user.memberships:
            target_org_id = current_user.memberships[0].organization_id
        else:
            raise ForbiddenError(
                message="User does not belong to any organization. Please create or join an organization."
            )

    # Find organization and verify active status
    stmt = (
        select(Organization)
        .options(selectinload(Organization.memberships))
        .where(
            (Organization.id == target_org_id) | (Organization.slug == target_org_id),
            Organization.is_active.is_(True),
        )
    )
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()

    if not org:
        raise NotFoundError(message=f"Organization '{target_org_id}' not found or deactivated.")

    # Find membership for current user in this organization
    mem_stmt = select(OrganizationMembership).where(
        OrganizationMembership.organization_id == org.id,
        OrganizationMembership.user_id == current_user.id,
    )
    user_membership = (await db.execute(mem_stmt)).scalar_one_or_none()

    if not user_membership:
        # Cross-tenant access attempted
        raise TenantMismatchError(
            message=f"Access denied: You are not a member of organization '{org.name}' ({org.slug})."
        )

    # Store resolved tenant context on request state for audit & logging
    request.state.organization_id = org.id
    request.state.tenant_role = user_membership.role.value

    return OrgContext(
        organization=org,
        membership=user_membership,
        role=user_membership.role,
        user=current_user,
    )


def require_org_role(min_role: MembershipRole) -> Callable:
    """Dependency factory enforcing minimum required role in active organization context."""

    async def _role_checker(
        context: OrgContext = Depends(get_org_context),
    ) -> OrgContext:
        if not has_sufficient_role(context.role, min_role):
            raise ForbiddenError(
                message=(
                    f"Action requires minimum '{min_role.value}' role in organization '{context.organization.slug}'. "
                    f"Current role: '{context.role.value}'."
                )
            )
        return context

    return _role_checker
