from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from typing import List

from app.core.database import get_db

from app.core.dependencies import require_super_admin
from app.api.v1.auth import get_current_user

from app.models.user import User

from app.models.activity_log import ActivityLog

from app.schemas.activity_log import (
    ActivityLogResponse,
    ActivityLogMyResponse,
)




router = APIRouter(
    prefix="/activity",
    tags=["Activity Log"]
)



@router.get(
    "/all",
    response_model=List[ActivityLogResponse]
)
def get_all_logs(
    db: Session = Depends(get_db),
    user: User = Depends(require_super_admin)
):

    logs = (
        db.query(
            ActivityLog,
            User.full_name.label("user_name"),
            User.email.label("user_email"),
        )
        .outerjoin(
            User,
            ActivityLog.user_id == User.id
        )
        .order_by(
            ActivityLog.created_at.desc()
        )
        .all()
    )


    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "user_name": user_name,
            "user_email": user_email,
            "action": log.action,
            "module": log.module,
            "target_id": log.target_id,
            "target_name": log.target_name,
            "description": log.description,
            "created_at": log.created_at,
        }
        for log, user_name, user_email in logs
        
    ]

@router.get(
    "/me",
    response_model=List[ActivityLogMyResponse]
)
def get_my_logs(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    return (
        db.query(ActivityLog)
        .filter(
            ActivityLog.user_id == user.id
        )
        .order_by(
            ActivityLog.created_at.desc()
        )
        .all()
    )

