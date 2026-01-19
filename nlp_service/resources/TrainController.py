from fastapi import APIRouter

router = APIRouter()


@router.post("/train")
async def train():
    """
    Stub for training trigger.
    In real use:
    - Export data from Admin Service
    - Run `rasa train`
    - Update training history
    """
    return {"status": "started", "message": "Training triggered successfully"}
