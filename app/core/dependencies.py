from fastapi import Depends, HTTPException, status

from app.api.v1.auth import get_current_user
from app.models.user import User


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Memastikan user ber-role admin atau super_admin"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak. Fitur ini membutuhkan hak akses Admin.",
        )
    return current_user


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """Memastikan user HANYA ber-role super_admin"""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak. Fitur ini khusus untuk Super Admin.",
        )
    return current_user
