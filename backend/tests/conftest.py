import warnings
import os
import pytest
import alembic

from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient
from databases import Database
from alembic.config import Config

from app.models.user import UserCreate, UserInDB
from app.db.repositories.users import UsersRepository


@pytest.fixture(scope="session")
def apply_migrations():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    os.environ["TESTING"] = "1"
    config = Config("alembic.ini")

    alembic.command.upgrade(config, "head")
    yield
    alembic.command.downgrade(config, "base")


@pytest.fixture
def app(apply_migrations: None) -> FastAPI:
    from app.api.server import get_application

    return get_application()


@pytest.fixture
def db(app: FastAPI) -> Database:
    return app.state._db


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    async with LifespanManager(app):
        async with AsyncClient(
            app=app,
            base_url="http://testserver",
            headers={"content-type": "application/json"}
        ) as client:
            yield client


@pytest.fixture
async def test_user(db: Database) -> UserInDB:
    new_user = UserCreate(
        username="username7",
        password="password1234567"
    )
    user_repo = UsersRepository(db)
    existing_user = await user_repo.get_user_by_username(username=new_user.username)
    if existing_user:
        return existing_user
    return await user_repo.register_new_user(new_user=new_user)
