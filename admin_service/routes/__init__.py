from fastapi import APIRouter

from admin_service.resources.HrmsController import router as hrmsRoute
from admin_service.resources.IntentsController import router as chatRoute
from admin_service.resources.LoginController import router as loginRoute

router = APIRouter()

router.include_router(chatRoute, prefix="/intents", tags=["Intents"])
router.include_router(hrmsRoute, prefix="/hrms", tags=["HRMS"])
router.include_router(loginRoute, prefix="/login", tags=["Login"])
