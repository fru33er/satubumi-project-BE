from fastapi import Depends, HTTPException, status

from app.api.v1.auth import get_current_user
from app.models.user import User

# Role yang diizinkan di sistem
ALLOWED_ROLES = {"admin", "super_admin", "client", "field_officer"}

# Role yang memiliki hak akses penulisan data proyek
ADMIN_ROLES = {"admin", "super_admin"}


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Memastikan user ber-role admin atau super_admin."""
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak. Fitur ini membutuhkan hak akses Admin.",
        )
    return current_user


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """Memastikan user HANYA ber-role super_admin."""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak. Fitur ini khusus untuk Super Admin.",
        )
    return current_user


def require_field_officer(current_user: User = Depends(get_current_user)) -> User:
    """
    Memastikan user ber-role field_officer, admin, atau super_admin.
    field_officer dapat submit laporan lapangan dan pengukuran pohon.
    """
    if current_user.role not in {"field_officer", "admin", "super_admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak. Fitur ini membutuhkan hak akses Field Officer atau Admin."
        )
    return current_user

