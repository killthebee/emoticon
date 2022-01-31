import pytest

from httpx import AsyncClient
from fastapi import FastAPI
from databases import Database
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.models.user import UserCreate, UserInDB
from app.db.repositories.users import UsersRepository

pytestmark = pytest.mark.asyncio


class TestUserRoutes:
    async def test_routes_exist(self, app: FastAPI, client: AsyncClient) -> None:
        new_user = {"username": "test_username", "password": "testpassword"}
        response = await client.post("/api/users/register_user", json={"new_user": new_user})
        assert response.status_code != HTTP_404_NOT_FOUND


class TestUserRegistration:
    async def test_users_can_register_successfully(
            self,
            app: FastAPI,
            client: AsyncClient,
            db: Database
    ) -> None:
        user_repo = UsersRepository(db)
        new_user = {"username": "test_username2", "password": "testpassword2"}

        user_in_db = await user_repo.get_user_by_username(username=new_user["username"])
        assert user_in_db is None

        response = await client.post(app.url_path_for("users:register-new-user"), json={"new_user": new_user})
        assert response.status_code == HTTP_201_CREATED

        user_in_db = await user_repo.get_user_by_username(username=new_user["username"])
        assert user_in_db is not None
        assert user_in_db.username == new_user["username"]

    @pytest.mark.parametrize(
        "attr, value, status_code",
        (
                ("username", "test_username2", 400),
                ("password", "testpassword2", 201),
                ("username", "test_username2", 400),
                ("username", "test_username5", 400),
        )
    )
    async def test_user_registration_fails_when_credentials_are_taken(
            self,
            app: FastAPI,
            client: AsyncClient,
            db: Database,
            attr: str,
            value: str,
            status_code: int,
    ) -> None:
        new_user = {"username": "test_username5", "password": "testpassword3"}
        new_user[attr] = value
        res = await client.post(app.url_path_for("users:register-new-user"), json={"new_user": new_user})
        assert res.status_code == status_code