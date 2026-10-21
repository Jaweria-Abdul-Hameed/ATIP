"""Organization request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, example="Acme Engineering")
    slug: str = Field(..., min_length=2, max_length=64, example="acme-engineering")


class OrganizationRead(BaseModel):
    id: str = Field(..., example="org_1234567890")
    slug: str = Field(..., example="acme-engineering")
    name: str = Field(..., example="Acme Engineering")
    billing_tier: str = Field(default="team", example="team")
    created_at: datetime
    updated_at: datetime


class MembershipRead(BaseModel):
    id: str = Field(..., example="mem_1234567890")
    user_id: str = Field(..., example="usr_1234567890")
    email: str = Field(..., example="alice@example.com")
    name: str = Field(..., example="Alice Smith")
    role: str = Field(..., example="admin")
    created_at: datetime
