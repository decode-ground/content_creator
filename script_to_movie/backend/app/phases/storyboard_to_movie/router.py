from fastapi import APIRouter

router = APIRouter(prefix="/api/phases/storyboard-to-movie", tags=["storyboard-to-movie"])

# TODO: Implement endpoints
# POST /{project_id}/prompts - Generate video prompts
# POST /{project_id}/generate - Generate video clips
# POST /{project_id}/assemble - Assemble final movie
# GET /{project_id}/status - Generation status
