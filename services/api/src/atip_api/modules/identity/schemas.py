"""Identity and User schemas."""

from pydantic import BaseModel, EmailStr, Field


class OrganizationSummary(BaseModel):
    id: str = Field(..., example="org_default123")
    slug: str = Field(..., example="acme-corp")
    name: str = Field(..., example="Acme Corporation")
    role: str = Field(..., example="owner")


class UserProfile(BaseModel):
    id: str = Field(..., example="usr_1234567890")
    email: EmailStr = Field(..., example="developer@atip.dev")
    name: str = Field(..., example="Lead Engineer")
    avatar_url: str | None = Field(
        default=None, example="https://avatars.githubusercontent.com/u/1?v=4"
    )
    is_active: bool = Field(default=True)
    organizations: list[OrganizationSummary] = Field(default_factory=list)
