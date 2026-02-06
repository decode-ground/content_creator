from fastapi import APIRouter

router = APIRouter(prefix="/api/phases/script-to-trailer", tags=["script-to-trailer"])

# TODO: Implement endpoints
# POST /{project_id}/analyze - Parse script
# POST /{project_id}/characters - Generate character consistency
# POST /{project_id}/settings - Generate setting consistency
# POST /{project_id}/select-scenes - Select trailer scenes
