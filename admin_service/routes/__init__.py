from fastapi import APIRouter

from admin_service.resources.IntentsController import router as chatRoute

router = APIRouter()

router.include_router(chatRoute, prefix="/intents", tags=["Intents"])
