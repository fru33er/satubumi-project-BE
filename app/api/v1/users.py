from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import require_super_admin
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["User Management (Super Admin Only)"])

@router.get("/", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db), super_admin: User = Depends(require_super_admin)):
    """[Super Admin Only] Ambil semua daftar pengguna"""
    return db.query(User).all()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_by_admin(
    user_in: UserCreate, 
    db: Session = Depends(get_db), 
    super_admin: User = Depends(require_super_admin)
):
    """[Super Admin Only] Buat akun user baru (Admin / Super Admin / Client)"""
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
