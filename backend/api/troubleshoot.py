from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["troubleshoot"])

@router.post("/troubleshoot")
async def troubleshoot():
    pass
