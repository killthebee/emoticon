import pytest

from httpx import AsyncClient
from fastapi import FastAPI

from starlette.status import HTTP_404_NOT_FOUND


class TestEmoticonRoutes:
    @pytest.mark.asyncio
    async def test_routes_exist(self, app: FastAPI, client: AsyncClient) -> None:
        response = await client.get("/api/fetch_emoticon/hmmm")
        assert response.status_code != HTTP_404_NOT_FOUND

