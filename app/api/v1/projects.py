
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["Monitor — Projects"])


def require_admin(current_user: User) -> User:
    """Dependency helper: pastikan user adalah admin atau super_admin."""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya admin atau super_admin yang dapat melakukan aksi ini.",
        )
    return current_user


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Membuat proyek monitoring baru.

    - Hanya **admin** dan **super_admin** yang dapat membuat proyek.
    - `boundary_geojson`: Batas wilayah proyek dalam format GeoJSON (opsional, bisa diisi nanti).
    - `targets_json`: Target proyek, contoh `{"restoration_ha": 1000, "tree_planting": 100000}`.
    """
    require_admin(current_user)

    project = Project(
        name=body.name,
        description=body.description,
        location_name=body.location_name,
        area_ha=body.area_ha,
        status=body.status or "active",
        boundary_geojson=body.boundary_geojson,
        targets_json=body.targets_json,
        created_by=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Mendapatkan daftar semua proyek monitoring.

    - **Admin/Super Admin**: Melihat semua proyek.
    - **Client/User lain**: Juga melihat semua proyek (read-only).
    """
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mendapatkan detail satu proyek berdasarkan ID."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan.")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mengupdate data proyek.

    - Hanya **admin** dan **super_admin** yang dapat mengupdate proyek.
    - Semua field bersifat opsional — hanya field yang dikirim yang diupdate.
    """
    require_admin(current_user)

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan.")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_200_OK)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Menghapus proyek beserta seluruh data monitornya (cascade).

    - Hanya **admin** dan **super_admin** yang dapat menghapus proyek.
    """
    require_admin(current_user)

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan.")

    db.delete(project)
    db.commit()
    return {"message": f"Proyek '{project.name}' berhasil dihapus."}
