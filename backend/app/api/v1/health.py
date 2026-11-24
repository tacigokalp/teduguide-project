"""GET /api/v1/health: is the server alive? Used by hosting and uptime monitoring."""
from fastapi import APIRouter

router = APIRouter()

VERSION = "0.1.0"


@router.get("/health")
async def health() -> dict[str, str]:
    # The database check is added in step A-07, when the tables exist.
    return {"status": "ok", "version": VERSION}
