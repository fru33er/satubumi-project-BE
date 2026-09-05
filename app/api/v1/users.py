import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.activity import create_activity_log
from app.core.database import get_db
from app.core.dependencies import require_admin, require_super_admin
from app.core.security import get_password_hash
from app.core.storage import (
    delete_public_file,
    extract_public_storage_path,
    upload_public_file,
)
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate

ALLOWED_ROLES = {"admin", "super_admin", "client", "field_officer"}
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("/", response_model=list[UserResponse])
def list_users(
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    return query.all()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    super_admin: User = Depends(require_super_admin),
):
    if user_in.role and user_in.role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Role tidak valid. Pilihan: {', '.join(ALLOWED_ROLES)}",
        )

    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar.")

    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        phone_number=user_in.phone_number,
        role=user_in.role or "admin",
    )

    db.add(new_user)
    db.flush()

    create_activity_log(
        db=db,
        user=super_admin,
        action="CREATE",
        module="USER",
        target_id=new_user.id,
        target_name=new_user.full_name,
        description="Membuat akun user baru",
    )

    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    usr = db.query(User).filter(User.id == user_id).first()
    if not usr:
        raise HTTPException(status_code=404, detail="User tidak ditemukan.")
    return usr


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    super_admin: User = Depends(require_super_admin),
):
    usr = db.query(User).filter(User.id == user_id).first()
    if not usr:
        raise HTTPException(status_code=404, detail="User tidak ditemukan.")

    if user_in.role and user_in.role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Role tidak valid. Pilihan: {', '.join(ALLOWED_ROLES)}",
        )

    update_data = user_in.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"] != usr.email:
        taken = (
            db.query(User)
            .filter(User.email == update_data["email"], User.id != user_id)
            .first()
        )
        if taken:
            raise HTTPException(status_code=400, detail="Email sudah terdaftar.")

    if "password" in update_data:
        usr.hashed_password = get_password_hash(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(usr, field, value)

    create_activity_log(
        db=db,
        user=super_admin,
        action="UPDATE",
        module="USER",
        target_id=usr.id,
        target_name=usr.full_name,
        description="Mengubah data user",
    )

    db.commit()
    db.refresh(usr)
    return usr


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    super_admin: User = Depends(require_super_admin),
):
    usr = db.query(User).filter(User.id == user_id).first()
    if not usr:
        raise HTTPException(status_code=404, detail="User tidak ditemukan.")

    create_activity_log(
        db=db,
        user=super_admin,
        action="DELETE",
        module="USER",
        target_id=usr.id,
        target_name=usr.full_name,
        description="Menghapus user",
    )

    db.delete(usr)
    db.commit()


@router.put("/{user_id}/profile-image")
async def upload_profile_image(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    super_admin: User = Depends(require_super_admin),
):
    usr = db.query(User).filter(User.id == user_id).first()
    if not usr:
        raise HTTPException(status_code=404, detail="User tidak ditemukan.")

    content_type = (file.content_type or "").lower()
    raw_name = (file.filename or "photo.jpg").lower()
    ext = f".{raw_name.rsplit('.', 1)[-1]}" if "." in raw_name else ""

    if content_type not in ALLOWED_IMAGE_TYPES or ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="File harus JPG, PNG, atau WEBP.",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="File kosong.")

    old_path = extract_public_storage_path(usr.profile_image)
    if old_path:
        try:
            delete_public_file(old_path)
        except Exception as exc:
            print("Supabase delete profile error:", exc)

    storage_path = f"users/{usr.id}/profile-{uuid.uuid4().hex}{ext}"
    public_url = upload_public_file(
        path=storage_path,
        file_bytes=file_bytes,
        content_type=content_type,
    )

    usr.profile_image = public_url

    create_activity_log(
        db=db,
        user=super_admin,
        action="UPLOAD",
        module="USER",
        target_id=usr.id,
        target_name=usr.full_name,
        description="Mengubah foto profil user",
    )

    db.commit()
    db.refresh(usr)

    return {
        "message": "Profile image updated",
        "profile_image": usr.profile_image,
    }