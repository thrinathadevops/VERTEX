from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import require_admin, get_current_active_user
from app.models.portfolio import Project, ProjectCategory
from app.models.user import User
from app.schemas.portfolio import ProjectCreate, ProjectResponse

router = APIRouter()

@router.get("/", response_model=list[ProjectResponse], summary="List all published projects")
async def list_projects(
    category: ProjectCategory | None = None,
    featured_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    q = select(Project).where(Project.is_published == True)
    if category:
        q = q.where(Project.category == category)
    if featured_only:
        q = q.where(Project.is_featured == True)
    result = await db.execute(
        q.order_by(
            Project.is_featured.desc(),
            Project.display_order.asc(),
            Project.created_at.desc(),
        )
    )
    return result.scalars().all()

@router.get("/{slug}", response_model=ProjectResponse, summary="Get project by slug")
async def get_project(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.slug == slug))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("/", response_model=ProjectResponse, status_code=201,
             summary="Create project (admin only)")
async def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    project = Project(**payload.model_dump(), created_by=current_user.id)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project

@router.patch("/{project_id}/feature", summary="Toggle featured flag (admin)")
async def toggle_feature(
    project_id: UUID,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Not found")
    project.is_featured = not project.is_featured
    await db.commit()
    return {"id": project_id, "is_featured": project.is_featured}

@router.delete("/{project_id}", status_code=204, summary="Delete project (admin)")
async def delete_project(
    project_id: UUID,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(project)
    await db.commit()
