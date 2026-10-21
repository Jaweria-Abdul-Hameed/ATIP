"""Organization management router."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.core.errors import NotFoundError
from atip_api.core.pagination import PaginationMetadata, PaginationParams, get_pagination_params
from atip_api.core.responses import DataResponse, PaginatedResponse
from atip_api.db.models import Organization
from atip_api.db.session import get_db
from atip_api.modules.organizations.schemas import (
    OrganizationCreate,
    OrganizationRead,
)

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("", response_model=PaginatedResponse[OrganizationRead])
async def list_organizations(
    pagination: PaginationParams = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[OrganizationRead]:
    """List organizations accessible to the current user."""
    # Query database organizations
    stmt = select(Organization).offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(stmt)
    orgs = result.scalars().all()

    # If database is fresh/empty in local dev, provide default workspace if none exist
    items = [
        OrganizationRead(
            id=org.id,
            slug=org.slug,
            name=org.name,
            billing_tier=org.billing_tier,
            created_at=org.created_at,
            updated_at=org.updated_at,
        )
        for org in orgs
    ]

    total = len(items)
    return PaginatedResponse(
        data=items,
        pagination=PaginationMetadata.create(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total,
        ),
    )


@router.post("", response_model=DataResponse[OrganizationRead], status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
) -> DataResponse[OrganizationRead]:
    """Create a new organization."""
    org = Organization(name=payload.name, slug=payload.slug)
    db.add(org)
    await db.flush()
    return DataResponse(
        data=OrganizationRead(
            id=org.id,
            slug=org.slug,
            name=org.name,
            billing_tier=org.billing_tier,
            created_at=org.created_at,
            updated_at=org.updated_at,
        )
    )


@router.get("/{id}", response_model=DataResponse[OrganizationRead])
async def get_organization(
    id: str,
    db: AsyncSession = Depends(get_db),
) -> DataResponse[OrganizationRead]:
    """Get organization by ID."""
    stmt = select(Organization).where(Organization.id == id)
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()
    if not org:
        raise NotFoundError(f"Organization '{id}' not found")

    return DataResponse(
        data=OrganizationRead(
            id=org.id,
            slug=org.slug,
            name=org.name,
            billing_tier=org.billing_tier,
            created_at=org.created_at,
            updated_at=org.updated_at,
        )
    )
