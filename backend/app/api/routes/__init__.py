from fastapi import APIRouter

from app.api.routes.emoticons import router as emoticon_router
from app.api.routes.users import router as users_router


router = APIRouter()


router.include_router(emoticon_router, prefix="/fetch_emoticon", tags=["emoticons"])
router.include_router(users_router, prefix="/users", tags=["users"])
