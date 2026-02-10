import logging
from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm import LLMClient, llm_client


class BaseAgent(ABC):
    """
    Base class for all pipeline agents.

    Every agent follows the same pattern:
    1. Receive a database session and a project_id
    2. Read the data it needs from the database
    3. Call the LLM (or external API) to process
    4. Write results back to the database
    5. Return a summary dict

    Subclasses MUST implement:
    - name: str property — unique identifier for this agent
    - execute(db, project_id) -> dict — the agent's main work
    """

    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm or llm_client
        self.logger = logging.getLogger(f"agent.{self.name}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this agent, e.g. 'script_analysis'."""
        ...

    @abstractmethod
    async def execute(self, db: AsyncSession, project_id: int) -> dict[str, Any]:
        """
        Run this agent's task.

        Args:
            db: Async database session (already open, do NOT close it)
            project_id: The project to operate on

        Returns:
            dict with at minimum {"status": "success" | "error", "message": str}
            Add any extra data relevant to the agent.

        Raises:
            Should NOT raise. Catch exceptions and return {"status": "error", ...}
        """
        ...

    async def safe_execute(self, db: AsyncSession, project_id: int) -> dict[str, Any]:
        """Wrapper that catches all exceptions. Used by the orchestrator."""
        try:
            self.logger.info(f"Starting {self.name} for project {project_id}")
            result = await self.execute(db, project_id)
            self.logger.info(
                f"Completed {self.name} for project {project_id}: {result.get('status')}"
            )
            return result
        except Exception as e:
            self.logger.error(
                f"Agent {self.name} failed for project {project_id}: {e}", exc_info=True
            )
            return {"status": "error", "message": str(e)}


# =============================================================================
# EXAMPLE AGENT (for reference — copy this pattern for your agents)
# =============================================================================
#
# from pydantic import BaseModel
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
#
# from app.models.project import Project
# from app.models.scene import Scene
# from app.phases.base_agent import BaseAgent
#
#
# # Step 1: Define a Pydantic model for the LLM's structured output
# class SceneExtraction(BaseModel):
#     title: str
#     description: str
#     dialogue: str
#     setting: str
#     characters: list[str]
#     duration: int
#
#
# class SceneListOutput(BaseModel):
#     scenes: list[SceneExtraction]
#
#
# class ExampleScriptAnalysisAgent(BaseAgent):
#     @property
#     def name(self) -> str:
#         return "example_script_analysis"
#
#     async def execute(self, db: AsyncSession, project_id: int) -> dict:
#         # Step 2: Read from database
#         result = await db.execute(select(Project).where(Project.id == project_id))
#         project = result.scalar_one_or_none()
#         if not project:
#             return {"status": "error", "message": "Project not found"}
#
#         # Step 3: Call LLM with structured output
#         scene_list = await self.llm.invoke_structured(
#             messages=[
#                 {
#                     "role": "user",
#                     "content": f"Break this script into scenes:\n\n{project.scriptContent}",
#                 }
#             ],
#             output_schema=SceneListOutput,
#             system="You are a screenplay analyst. Break the script into distinct scenes.",
#         )
#
#         # Step 4: Write results to database
#         import json
#         for i, scene_data in enumerate(scene_list.scenes):
#             scene = Scene(
#                 projectId=project_id,
#                 sceneNumber=i + 1,
#                 title=scene_data.title,
#                 description=scene_data.description,
#                 dialogue=scene_data.dialogue,
#                 setting=scene_data.setting,
#                 characters=json.dumps(scene_data.characters),
#                 duration=scene_data.duration,
#                 order=i + 1,
#             )
#             db.add(scene)
#
#         await db.commit()
#
#         # Step 5: Return summary
#         return {
#             "status": "success",
#             "message": f"Extracted {len(scene_list.scenes)} scenes",
#             "scenes_created": len(scene_list.scenes),
#         }
