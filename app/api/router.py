from fastapi import APIRouter

from app.api.products import router as products_router
from app.api.agent import router as agents_router
from app.core.config import get_settings


settings = get_settings()

api_router = APIRouter(prefix=settings.api_v1_prefix)
api_router.include_router(products_router)
api_router.include_router(agents_router)
