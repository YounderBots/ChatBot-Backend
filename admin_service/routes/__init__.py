from fastapi import APIRouter

from admin_service.resources.AdminController import router as chatRoute

router = APIRouter()

router.include_router(chatRoute, prefix="/admin", tags=["Admin"])
