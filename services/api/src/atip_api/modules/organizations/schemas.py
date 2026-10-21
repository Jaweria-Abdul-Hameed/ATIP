"""Organization, membership, and invitation request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from atip_api.db.models.organization import MembershipRole


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, example="Acme Engineering")
    slug: str = Field(..., min_length=2, max_length=64, example="acme-engineering")
    billing_tier: str = Field(default="team", example="team")


class OrganizationRead(BaseModel):
    id: str = Field(..., example="org_1234567890")
    slug: str = Field(..., example="acme-engineering")
    name: str = Field(..., example="Acme Engineering")
    billing_tier: str = Field(default="team", example="team")
    role: str | None = Field(default=None, example="owner")
    created_at: datetime
    updated_at: datetime


class MembershipRead(BaseModel):
    id: str = Field(..., example="mem_1234567890")
    user_id: str = Field(..., example="usr_1234567890")
    email: str = Field(..., example="alice@example.com")
    name: str = Field(..., example="Alice Smith")
    avatar_url: str | None = Field(default=None)
    role: str = Field(..., example="admin")
    created_at: datetime


class MembershipUpdate(BaseModel):
    role: MembershipRole = Field(..., example=MembershipRole.ADMIN)


class InvitationCreate(BaseModel):
    email: EmailStr = Field(..., example="newengineer@atip.dev")
    role: MembershipRole = Field(default=MembershipRole.DEVELOPER, example=MembershipRole.DEVELOPER)


class InvitationRead(BaseModel):
    id: str = Field(..., example="inv_1234567890")
    organization_id: str = Field(..., example="org_1234567890")
    email: str = Field(..., example="newengineer@atip.dev")
    role: str = Field(..., example="developer")
    invited_by_user_id: str = Field(..., example="usr_1234567890")
    token: str = Field(..., example="inv_tok_abcdef123456")
    expires_at: datetime
    created_at: datetime


class InvitationAcceptResponse(BaseModel):
    success: bool = True
    organization_id: str
    organization_name: str
    role: str
    message: str = "Invitation accepted successfully."
