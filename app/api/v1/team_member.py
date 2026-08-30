from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    status,
)

from sqlalchemy.orm import Session

import os
import shutil

from typing import List

from app.core.database import get_db
from app.core.dependencies import require_super_admin
from app.core.activity import create_activity_log

from app.models.team_member import TeamMember
from app.schemas.team_member import (
    TeamMemberCreate,
    TeamMemberUpdate,
    TeamMemberResponse,
)

from app.models.user import User


router = APIRouter(
    prefix="/team-members",
    tags=["Team Members"],
)


@router.get("/", response_model=List[TeamMemberResponse])
def list_team_members(db: Session = Depends(get_db)):
    return (
        db.query(TeamMember)
        .filter(TeamMember.is_active == True)
        .order_by(TeamMember.order.asc())
        .all()
    )


@router.get("/{member_id}", response_model=TeamMemberResponse)
def get_team_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(TeamMember).filter(TeamMember.id == member_id).first()

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Team member tidak ditemukan",
        )

    return member


@router.post(
    "/",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_team_member(
    data: TeamMemberCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    member = TeamMember(
        name=data.name,
        role=data.role,
        description=data.description,
        order=data.order,
        is_active=data.is_active,
    )

    db.add(member)
    db.flush()

    create_activity_log(
        db=db,
        user=admin,
        action="CREATE",
        module="TEAM_MEMBER",
        target_id=member.id,
        target_name=member.name,
        description="Menambahkan team member",
    )

    db.commit()
    db.refresh(member)

    return member


@router.put("/{member_id}", response_model=TeamMemberResponse)
def update_team_member(
    member_id: int,
    data: TeamMemberUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    member = db.query(TeamMember).filter(TeamMember.id == member_id).first()

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Team member tidak ditemukan",
        )

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(member, field, value)

    create_activity_log(
        db=db,
        user=admin,
        action="UPDATE",
        module="TEAM_MEMBER",
        target_id=member.id,
        target_name=member.name,
        description="Mengubah team member",
    )

    db.commit()
    db.refresh(member)

    return member


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team_member(
    member_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    member = db.query(TeamMember).filter(TeamMember.id == member_id).first()

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Team member tidak ditemukan",
        )

    create_activity_log(
        db=db,
        user=admin,
        action="DELETE",
        module="TEAM_MEMBER",
        target_id=member.id,
        target_name=member.name,
        description="Menghapus team member",
    )

    db.delete(member)
    db.commit()


@router.post("/{member_id}/image")
async def upload_team_image(
    member_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    member = db.query(TeamMember).filter(TeamMember.id == member_id).first()

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Team member tidak ditemukan",
        )

    upload_dir = "static/team"
    os.makedirs(upload_dir, exist_ok=True)

    filename = f"team_{member_id}_{file.filename}"
    path = f"{upload_dir}/{filename}"

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    member.image_url = "/" + path

    create_activity_log(
        db=db,
        user=admin,
        action="UPLOAD",
        module="TEAM_MEMBER_IMAGE",
        target_id=member.id,
        target_name=member.name,
        description="Mengubah foto team member",
    )

    db.commit()
    db.refresh(member)

    return {
        "message": "Image uploaded",
        "image_url": member.image_url,
    }