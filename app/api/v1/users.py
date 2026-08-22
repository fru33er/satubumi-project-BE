from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import require_super_admin
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate

# Role yang diizinkan di sistem
ALLOWED_ROLES = {"admin", "super_admin", "client"}

router = APIRouter(prefix="/users", tags=["User Management (Super Admin Only)"])


@router.get("/", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db), super_admin: User = Depends(require_super_admin)):
    """[Super Admin Only] Ambil semua daftar pengguna"""
    return db.query(User).all()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    super_admin: User = Depends(require_super_admin)
):
    """[Super Admin Only] Buat akun user baru (admin / super_admin / client)"""
    if user_in.role and user_in.role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Role tidak valid. Pilihan: {', '.join(ALLOWED_ROLES)}"
        )
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar.")

    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        phone_number=user_in.phone_number,
        role=user_in.role or "admin"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    super_admin: User = Depends(require_super_admin)
):
    """[Super Admin Only] Ambil detail satu user berdasarkan ID"""
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
    """[Super Admin Only] Update data user (email, nama, role, password, dll)"""
    usr = db.query(User).filter(User.id == user_id).first()
    if not usr:
        raise HTTPException(status_code=404, detail="User tidak ditemukan.")

    if user_in.role and user_in.role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Role tidak valid. Pilihan: {', '.join(ALLOWED_ROLES)}",
        )

    update_data = user_in.model_dump(exclude_unset=True)

    # Email baru harus unik
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

    db.commit()
    db.refresh(usr)
    return usr


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    super_admin: User = Depends(require_super_admin)
):
    """[Super Admin Only] Hapus akun user"""
    usr = db.query(User).filter(User.id == user_id).first()
    if not usr:
        raise HTTPException(status_code=404, detail="User tidak ditemukan.")
    db.delete(usr)
    db.commit()

