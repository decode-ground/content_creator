from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.schemas.project import ProjectCreate


async def create_project(db: AsyncSession, data: ProjectCreate, user_id: int) -> Project:
    project = Project(
        userId=user_id,
        title=data.title,
        description=data.description,
        scriptContent=data.scriptContent,
        status="draft",
        progress=0,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def list_projects(db: AsyncSession, user_id: int | None = None) -> list[Project]:
    query = select(Project).order_by(Project.createdAt.desc())
    if user_id:
        query = query.where(Project.userId == user_id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_project(db: AsyncSession, project_id: int) -> Project | None:
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()
