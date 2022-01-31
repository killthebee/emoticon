import pytest
import jwt

from httpx import AsyncClient
from fastapi import FastAPI
from pydantic import ValidationError
from starlette.datastructures import Secret
from databases import Database
from typing import Union, Type

from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND

from app.models.user import UserCreate, UserInDB
from app.db.repositories.users import UsersRepository
from app.services import auth_service
from app.core.config import SECRET_KEY, JWT_ALGORITHM, JWT_AUDIENCE, JWT_TOKEN_PREFIX, ACCESS_TOKEN_EXPIRE_MINUTES
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
        response = await client.post(app.url_path_for("users:register-new-user"), json={"new_user": new_user})
        assert response.status_code == status_code

    async def test_users_saved_password_is_hashed(
            self,
            app: FastAPI,
            client: AsyncClient,
            db: Database
    ) -> None:
        user_repo = UsersRepository(db)
        new_user = {"username": "test_username6", "password": "testpassword4"}
        response = await client.post(app.url_path_for("users:register-new-user"), json={"new_user": new_user})
        assert response.status_code == HTTP_201_CREATED
        user_in_db = await user_repo.get_user_by_username(username=new_user["username"])
        assert user_in_db is not None
        assert user_in_db.password != new_user["password"]
        assert auth_service.verify_password(
            password=new_user["password"],
            hashed_password=user_in_db.password,
        )


class TestAuthTokens:
    async def test_create_access_token_successfully(
            self, app: FastAPI, client: AsyncClient, test_user: UserInDB
    ) -> None:
        access_token = auth_service.create_access_token_for_user(
            user=test_user,
            secret_key=str(SECRET_KEY),
            audience=JWT_AUDIENCE,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES
        )
        creds = jwt.decode(access_token, str(SECRET_KEY), audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM])
        assert creds.get("username") is not None
        assert creds["username"] == test_user.username
        assert creds["aud"] == JWT_AUDIENCE

    async def test_token_missing_user_is_invalid(self, app: FastAPI, client: AsyncClient) -> None:
        access_token = auth_service.create_access_token_for_user(
            user=None,
            secret_key=str(SECRET_KEY),
            audience=JWT_AUDIENCE,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        with pytest.raises(jwt.PyJWTError):
            jwt.decode(access_token, str(SECRET_KEY), audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM])

    @pytest.mark.parametrize(
        "secret_key, jwt_audience, exception",
        (
                ("wrong-secret", JWT_AUDIENCE, jwt.InvalidSignatureError),
                (None, JWT_AUDIENCE, jwt.InvalidSignatureError),
                (SECRET_KEY, "othersite:auth", jwt.InvalidAudienceError),
                (SECRET_KEY, None, ValidationError),
        )
    )
    async def test_invalid_token_content_raises_error(
            self,
            app: FastAPI,
            client: AsyncClient,
            test_user: UserInDB,
            secret_key: Union[str, Secret],
            jwt_audience: str,
            exception: Type[BaseException],
    ) -> None:
        with pytest.raises(exception):
            access_token = auth_service.create_access_token_for_user(
                user=test_user,
                secret_key=str(secret_key),
                audience=jwt_audience,
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES,
            )
            jwt.decode(access_token, str(SECRET_KEY), audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM])


class TestUserLogin:
    async def test_user_can_login_successfully_and_receives_valid_token(
        self, app: FastAPI, client: AsyncClient, test_user: UserInDB,
    ) -> None:
        client.headers["content-type"] = "application/x-www-form-urlencoded"
        login_data = {
            "username": test_user.username,
            "password": "password1234567",
        }
        res = await client.post(app.url_path_for("users:login-username-and-password"), data=login_data)
        assert res.status_code == HTTP_200_OK

        token = res.json().get("access_token")
        creds = jwt.decode(token, str(SECRET_KEY), audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM])
        assert "username" in creds
        assert creds["username"] == test_user.username
        assert "token_type" in res.json()
        assert res.json().get("token_type") == "bearer"

    @pytest.mark.parametrize(
        "credential, wrong_value, status_code",
        (
            ("username", "lalalala", 401),
            ("username", None, 401),
            ("username", "hm", 401),
            ("password", "pw", 401),
            ("password", None, 401),
        ),
    )
    async def test_user_with_wrong_creds_doesnt_receive_token(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_user: UserInDB,
        credential: str,
        wrong_value: str,
        status_code: int,
    ) -> None:
        client.headers["content-type"] = "application/x-www-form-urlencoded"
        user_data = test_user.dict()
        user_data["password"] = "password1234567"
        user_data[credential] = wrong_value
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"],
        }
        res = await client.post(app.url_path_for("users:login-username-and-password"), data=login_data)
        assert res.status_code == status_code
        assert "access_token" not in res.json()
