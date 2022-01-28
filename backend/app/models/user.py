import string

from typing import Optional
from pydantic import constr, validator

from app.models.core import IDModelMixin, CoreModel
from app.models.token import AccessToken


def validate_username(username: str) -> str:
    allowed = string.ascii_letters + string.digits + '-' + '_'
    assert all(char in allowed for char in username), "Invalid characters in username."
    assert len(username) >= 3, "Username must be 3 characters or more."
    return username


class UserBase(CoreModel):
    username: Optional[str]


class UserCreate(CoreModel):
    password: constr(min_length=7, max_length=150)
    username: str

    @validator("username", pre=True)
    def username_is_valid(cls, username: str) -> str:
        return validate_username(username)


class UserPasswordUpdate(CoreModel):
    password: constr(min_length=7, max_length=100)


class UserInDB(IDModelMixin, UserBase):
    password: constr(min_length=7, max_length=150)


class UserPublic(IDModelMixin, UserBase):
    access_token: Optional[AccessToken]
