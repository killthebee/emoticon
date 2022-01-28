from fastapi import HTTPException, status
from databases import Database
from typing import Optional

from app.db.repositories.base import BaseRepository
from app.models.user import UserCreate, UserInDB
from app.services import auth_service


GET_USER_BY_USERNAME_QUERY = """
    SELECT id, username, password
    FROM users
    WHERE username = :username;
"""
REGISTER_NEW_USER_QUERY = """
    INSERT INTO users (username, password)
    VALUES (:username, :password)
    RETURNING id, username, password;
"""


class UsersRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.auth_service = auth_service

    async def get_user_by_username(self, *, username: str) -> UserInDB:
        user_record = await self.db.fetch_one(query=GET_USER_BY_USERNAME_QUERY, values={"username": username})

        if not user_record:
            return None

        return UserInDB(**user_record)

    async def register_new_user(self, *, new_user: UserCreate) -> UserInDB:
        if await self.get_user_by_username(username=new_user.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="That username is already taken. Please try another one."
            )

        user_password_update = self.auth_service.create_hashed_password(plaintext_password=new_user.password)
        new_user_params = new_user.copy(update=user_password_update.dict())
        created_user = await self.db.fetch_one(query=REGISTER_NEW_USER_QUERY, values=new_user_params.dict())
        return UserInDB(**created_user)

    async def authenticate_user(self, *, username: str, password: str) -> Optional[UserInDB]:
        user = await self.get_user_by_username(username=username)
        if not user:
            return None
        if not self.auth_service.verify_password(password=password, hashed_password=user.password):
            return None
        return user