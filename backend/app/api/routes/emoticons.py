import httpx
import asyncio
import aiofiles

from typing import List
from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide

from app.redis.containers import Container
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
        service: Service = Depends(Provide[Container.service])
) -> List[dict]:
    #
    if not await service.get_emoticon_word(emoticon_word):
        await handle_new_emoticon(emoticon_word, service)
    cleanings = [
        {"id": 1, "name": "My house", "cleaning_type": "full_clean", "price_per_hour": 29.99},
        {"id": 2, "name": "Someone else's house", "cleaning_type": "spot_clean", "price_per_hour": 19.99}
    ]
    return cleanings


container = Container()
container.config.redis_host.from_env("REDIS_HOST", "redis")
container.config.redis_password.from_env("REDIS_PASSWORD", "password")
container.wire(modules=[__name__])
