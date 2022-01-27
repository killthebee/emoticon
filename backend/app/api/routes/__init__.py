from fastapi import APIRouter

from app.api.routes.emoticons import router as cleanings_router


router = APIRouter()


router.include_router(cleanings_router, prefix="/fetch_emoticon", tags=["emoticon"])
