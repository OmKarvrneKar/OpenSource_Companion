# ── routers/contributions.py ────────────────────────────────────
# Contribution verification endpoint
# ────────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas.contributions import (
    ContributionCheckRequest,
    ContributionCheckResponse,
    ContributionCheckData,
)
from app.services.contribution_service import check_contribution

router = APIRouter()


@router.post("/check", response_model=ContributionCheckResponse)
def verify_contribution(
    body: ContributionCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check if a PR was merged for the user's enrollment.
    Currently mocked — always marks as completed.
    """
    enrollment = check_contribution(db, current_user.id, body.enrollment_id)

    return ContributionCheckResponse(
        message="Contribution verified",
        data=ContributionCheckData(status=enrollment.status.value),
    )
