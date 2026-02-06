from fastapi import APIRouter

router = APIRouter(prefix="/api/workflow", tags=["workflow"])

# TODO: Implement endpoints
# POST /{project_id}/start - Start full pipeline
# GET /{project_id}/status - Get status
# POST /{project_id}/pause - Pause
# POST /{project_id}/resume - Resume
