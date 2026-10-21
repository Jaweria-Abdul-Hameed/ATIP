"""Identity and current user session router."""

from fastapi import APIRouter, Request

from atip_api.core.responses import DataResponse
from atip_api.modules.identity.schemas import OrganizationSummary, UserProfile

router = APIRouter(prefix="/me", tags=["Identity"])


@router.get("", response_model=DataResponse[UserProfile])
async def get_current_user(request: Request) -> DataResponse[UserProfile]:
    """Retrieve profile and organizations for the authenticated user."""
    # In M1 baseline, return authenticated session context
    profile = UserProfile(
        id="usr_current_engineer",
        email="developer@atip.dev",
        name="Lead Engineer",
        avatar_url=None,
        is_active=True,
        organizations=[
            OrganizationSummary(
                id="org_default_workspace",
                slug="default-workspace",
                name="Default Workspace",
                role="owner",
            )
        ],
    )
    return DataResponse(data=profile)
