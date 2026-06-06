from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["confluence"])

@router.post("/sync-confluence")
async def sync_confluence():
    pass
