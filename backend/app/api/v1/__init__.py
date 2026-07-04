# mypy: disable-error-code="no-untyped-def"
from fastapi import APIRouter
from .endpoints import auth_router
from .health import router as health_router
from .models import router as models_router

router = APIRouter()

router.include_router(health_router, tags=['健康检查'])
router.include_router(auth_router, prefix='/auth', tags=['用户认证'])
router.include_router(models_router, prefix='/models', tags=['模型管理'])
