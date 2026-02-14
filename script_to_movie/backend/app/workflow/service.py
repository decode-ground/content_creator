import logging

from app.core.database import AsyncSessionLocal
from app.phases.script_to_trailer.service import run_phase1

logger = logging.getLogger(__name__)


async def start_workflow(project_id: int, workflow_type: str) -> None:
    """Background task that runs the full pipeline.

    Uses its own DB session since it runs detached from the request lifecycle.
    """
    logger.info(f"Workflow '{workflow_type}' starting for project {project_id}")

    async with AsyncSessionLocal() as db:
        try:
            if workflow_type == "full_pipeline":
                # Phase 1: Script to Trailer
                await run_phase1(db, project_id)

                # Phase 2 & 3 will be added by other developers
                logger.info(f"Workflow complete for project {project_id}")
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")

        except Exception as e:
            logger.error(f"Workflow failed for project {project_id}: {e}")
            # Error status is already set by run_phase1's error handler
