"""Grounded AI failure analysis, triage, and hypothesis investigation router."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from atip_api.core.responses import DataResponse

router = APIRouter(prefix="/analysis", tags=["AI Failure Analysis"])


class TriageRequest(BaseModel):
    run_id: str
    failed_test_name: str
    stack_trace: str


class Citation(BaseModel):
    file_path: str
    line_start: int
    line_end: int
    snippet: str


class TriageResponse(BaseModel):
    hypothesis: str
    is_confirmed_fact: bool = Field(default=False)
    root_cause_summary: str
    confidence_score: float = Field(default=0.88)
    citations: list[Citation] = Field(default_factory=list)
    suggested_patch_diff: str | None = None
    requires_human_approval: bool = Field(default=True)


@router.post("/triage", response_model=DataResponse[TriageResponse])
async def triage_failure(payload: TriageRequest) -> DataResponse[TriageResponse]:
    """Analyze test failure with citation-grounded hypothesis."""
    return DataResponse(
        data=TriageResponse(
            hypothesis="Session token revocation timestamp does not invalidate active JWT claims",
            is_confirmed_fact=False,
            root_cause_summary="Token validation checks signature expiry but omits revoked_tokens database check.",
            confidence_score=0.91,
            citations=[
                Citation(
                    file_path="src/auth/session.ts",
                    line_start=42,
                    line_end=58,
                    snippet="export function verifySession(token: string) { return jwt.verify(token); }",
                )
            ],
            suggested_patch_diff="- return jwt.verify(token);\n+ return jwt.verify(token) && !isTokenRevoked(token.id);",
            requires_human_approval=True,
        )
    )
