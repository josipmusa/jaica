from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
def status_endpoint():
    return {"status": "ok"}