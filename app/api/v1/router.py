from fastapi import APIRouter

from app.api.v1 import auth, cycle, mental, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(cycle.router, prefix="/cycle", tags=["cycle"])
api_router.include_router(mental.router, prefix="/mental", tags=["mental"])
