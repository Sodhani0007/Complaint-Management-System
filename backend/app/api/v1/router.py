from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.complaints import router as complaints_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(complaints_router)
api_router.include_router(auth_router)
