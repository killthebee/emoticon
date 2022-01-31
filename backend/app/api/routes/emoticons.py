import httpx
import asyncio
import aiofiles

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from dependency_injector.wiring import inject, Provide

from app.redis.containers import Container
from app.models.user import UserInDB
from app.api.dependencies.auth import get_current_user
from app.redis.services import Service

router = APIRouter()


async def fetch_emoticon(emoticon_word: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://emoticon:8080/monster/{emoticon_word}")
        return response.content


async def save_image(emoticon_word: str, image):
    async with aiofiles.open(f"media/{emoticon_word}.png", 'wb') as f:
        await f.write(image)


async def handle_new_emoticon(emoticon_word, service):
    await asyncio.gather(
        save_image(emoticon_word, await fetch_emoticon(emoticon_word)),
        service.save_emoticon_word(emoticon_word)
    )


@router.get("/{emoticon_word}")
@inject
async def emoticons(
        emoticon_word: str,
        service: Service = Depends(Provide[Container.service]),
        current_user: UserInDB = Depends(get_current_user)
) -> RedirectResponse:
    if not await service.get_emoticon_word(emoticon_word):
        await handle_new_emoticon(emoticon_word, service)
    return RedirectResponse(f"http://127.0.0.1/emoticon_files/{emoticon_word}.png")


container = Container()
container.config.redis_host.from_env("REDIS_HOST", "redis")
container.config.redis_password.from_env("REDIS_PASSWORD", "password")
container.wire(modules=[__name__])
