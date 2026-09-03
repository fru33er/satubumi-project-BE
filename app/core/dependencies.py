from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.monitor import ProjectMember

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


def get_project_or_404(
    project_id: int,
    db: Session,
    current_user: Optional[User] = None
) -> Project:
    """
    Mendapatkan project berdasarkan project_id dan memvalidasi hak akses:
    - Jika project tidak ditemukan -> 404
    - Jika current_user disediakan dan bukan admin/super_admin:
      cek apakah user terdaftar di tabel project_members.
      Jika tidak terdaftar -> 403 Forbidden
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan.")

    if current_user and current_user.role not in ADMIN_ROLES:
        is_member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id
        ).first()
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Akses ditolak. Anda bukan anggota dari proyek ini."
            )

    return project

