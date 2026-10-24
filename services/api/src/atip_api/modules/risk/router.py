"""Risk intelligence, explainable defect scoring, impact propagation, and test selection router."""

import logging

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.core.errors import ForbiddenError, NotFoundError
from atip_api.core.responses import DataResponse
from atip_api.db.models.organization import OrganizationMembership, User
from atip_api.db.models.repository import Repository
from atip_api.db.session import get_db
from atip_api.modules.identity.deps import get_current_active_user
from atip_api.modules.risk.schemas import (
    ChangeImpactNode,
    FileRiskAssessmentRead,
    RiskAssessmentSummaryRead,
    RiskEvaluateRequest,
)
from atip_api.modules.risk.service import RiskAssessmentService
from atip_api.modules.risk.test_selector import TestSelectionResult

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Risk Intelligence"])

_risk_service = RiskAssessmentService()


def _extract_org_id(request: Request, current_user: User) -> str:
    """Extract organization ID from header or user's active membership."""
    header_org = request.headers.get("X-Organization-ID")
    if header_org:
        return header_org
    if current_user.memberships:
        return current_user.memberships[0].organization_id
    raise ForbiddenError("User is not a member of any organization")


async def _verify_repo_access(
    session: AsyncSession, repo_id: str, org_id: str, user_id: str
) -> Repository:
    """Verify tenant isolation and user authorization to access repository."""
    mem_stmt = select(OrganizationMembership).where(
        OrganizationMembership.organization_id == org_id,
        OrganizationMembership.user_id == user_id,
    )
    mem = (await session.execute(mem_stmt)).scalar_one_or_none()
    if not mem:
        raise ForbiddenError("You do not have access to this organization")

    repo_stmt = select(Repository).where(
        Repository.id == repo_id,
        Repository.organization_id == org_id,
    )
    repo = (await session.execute(repo_stmt)).scalar_one_or_none()
    if not repo:
        raise NotFoundError("Repository not found")
    return repo


@router.get(
    "/repositories/{id}/risks",
    response_model=DataResponse[RiskAssessmentSummaryRead],
)
async def get_repository_risks(
    id: str,
    commit_sha: str | None = Query(None, description="Specific commit SHA to evaluate"),
    branch: str = Query("main", description="Target branch"),
    force_recompute: bool = Query(False, description="Bypass cache and force fresh evaluation"),
    request: Request = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[RiskAssessmentSummaryRead]:
    """
    Get versioned explainable risk score, ranked files, and breakdown for a repository commit.
    Grounded in mined AST complexity, git churn, dependency blast radius, and defect history.
    """
    org_id = _extract_org_id(request, current_user)
    await _verify_repo_access(db, id, org_id, current_user.id)

    summary = await _risk_service.get_or_create_assessment(
        session=db,
        org_id=org_id,
        repository_id=id,
        commit_sha=commit_sha,
        branch=branch,
        force_recompute=force_recompute,
    )
    return DataResponse(data=summary)


@router.post(
    "/repositories/{id}/risks/evaluate",
    response_model=DataResponse[RiskAssessmentSummaryRead],
)
async def evaluate_repository_risks(
    id: str,
    payload: RiskEvaluateRequest,
    request: Request = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[RiskAssessmentSummaryRead]:
    """Trigger an on-demand fresh deterministic risk evaluation for a commit snapshot."""
    org_id = _extract_org_id(request, current_user)
    await _verify_repo_access(db, id, org_id, current_user.id)

    summary = await _risk_service.compute_and_persist_assessment(
        session=db,
        org_id=org_id,
        repository_id=id,
        commit_sha=payload.commit_sha,
        branch=payload.branch or "main",
    )
    return DataResponse(data=summary)


@router.get(
    "/repositories/{id}/risks/files/{file_path:path}",
    response_model=DataResponse[FileRiskAssessmentRead],
)
async def get_file_risk_detail(
    id: str,
    file_path: str,
    commit_sha: str | None = Query(None),
    request: Request = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[FileRiskAssessmentRead]:
    """Get detailed explainable factor breakdown and evidence drilldown for a specific file."""
    org_id = _extract_org_id(request, current_user)
    await _verify_repo_access(db, id, org_id, current_user.id)

    summary = await _risk_service.get_or_create_assessment(
        session=db,
        org_id=org_id,
        repository_id=id,
        commit_sha=commit_sha,
    )

    for f in summary.files:
        if f.file_path == file_path:
            return DataResponse(data=f)

    raise NotFoundError(f"File '{file_path}' was not found in risk assessment for repository '{id}'")


@router.get(
    "/repositories/{id}/risks/impact",
    response_model=DataResponse[list[ChangeImpactNode]],
)
async def get_change_impact_propagation(
    id: str,
    commit_sha: str | None = Query(None),
    branch: str = Query("main"),
    request: Request = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[list[ChangeImpactNode]]:
    """Get bounded transitive change-impact propagation graph for changed files."""
    org_id = _extract_org_id(request, current_user)
    await _verify_repo_access(db, id, org_id, current_user.id)

    summary = await _risk_service.get_or_create_assessment(
        session=db,
        org_id=org_id,
        repository_id=id,
        commit_sha=commit_sha,
        branch=branch,
    )
    return DataResponse(data=summary.impacted_nodes)


@router.get(
    "/repositories/{id}/risks/test-selection",
    response_model=DataResponse[TestSelectionResult],
)
async def get_impacted_test_selection(
    id: str,
    commit_sha: str | None = Query(None),
    request: Request = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[TestSelectionResult]:
    """
    Select impacted regression tests based on change propagation,
    flag unmonitored test gaps, and identify test flakiness signals.
    """
    org_id = _extract_org_id(request, current_user)
    await _verify_repo_access(db, id, org_id, current_user.id)

    result = await _risk_service.get_test_selection(
        session=db,
        org_id=org_id,
        repository_id=id,
        commit_sha=commit_sha,
    )
    return DataResponse(data=result)
