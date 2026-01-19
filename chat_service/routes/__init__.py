from fastapi import APIRouter
from resources.ChatController import router as chatRoute

router = APIRouter()

router.include_router(chatRoute, prefix="/chat", tags=["Chat"])
