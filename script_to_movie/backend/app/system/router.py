from fastapi import APIRouter

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
