from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.scene import Scene
from app.models.character import Character
from app.models.setting import Setting
from app.models.storyboard import StoryboardImage
from app.models.final_movie import FinalMovie
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


async def get_scenes(db: AsyncSession, project_id: int) -> list[Scene]:
    result = await db.execute(
        select(Scene).where(Scene.projectId == project_id).order_by(Scene.order)
    )
    return list(result.scalars().all())


async def get_characters(db: AsyncSession, project_id: int) -> list[Character]:
    result = await db.execute(
        select(Character).where(Character.projectId == project_id)
    )
    return list(result.scalars().all())


async def get_settings(db: AsyncSession, project_id: int) -> list[Setting]:
    result = await db.execute(
        select(Setting).where(Setting.projectId == project_id)
    )
    return list(result.scalars().all())


async def get_storyboards(db: AsyncSession, project_id: int) -> list[StoryboardImage]:
    result = await db.execute(
        select(StoryboardImage).where(StoryboardImage.projectId == project_id)
    )
    return list(result.scalars().all())


async def get_final_movie(db: AsyncSession, project_id: int) -> FinalMovie | None:
    result = await db.execute(
        select(FinalMovie).where(FinalMovie.projectId == project_id)
    )
    return result.scalar_one_or_none()
