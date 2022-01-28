from fastapi import Depends, APIRouter, HTTPException, Path, Body
from fastapi.security import OAuth2PasswordRequestForm
from starlette.status import HTTP_201_CREATED, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND

from app.api.dependencies.database import get_repository
from app.models.user import UserCreate, UserPublic, UserInDB, UserPublic
from app.models.token import AccessToken
from app.db.repositories.users import UsersRepository
from app.services import auth_service
from app.api.dependencies.auth import get_current_user


router = APIRouter()


@router.post("/register_user", name="users:register-new-user", response_model=UserPublic, status_code=HTTP_201_CREATED)
async def register_new_user(
        new_user: UserCreate = Body(..., embed=True),
        user_repo: UsersRepository = Depends(get_repository(UsersRepository))
) -> UserPublic:
    created_user = await user_repo.register_new_user(new_user=new_user)
    access_token = AccessToken(
        access_token=auth_service.create_access_token_for_user(user=created_user), token_type="bearer"
    )
    return UserPublic(**created_user.dict(), access_token=access_token)


@router.post("/login/token/", response_model=AccessToken, name="users:login-username-and-password")
async def user_login_with_username_and_password(
        user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
        form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm)
) -> AccessToken:
    user = await user_repo.authenticate_user(username=form_data.username, password=form_data.password)

    if not user:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Authentication was unsuccessful.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = AccessToken(access_token=auth_service.create_access_token_for_user(user=user), token_type="bearer")
    return access_token


@router.get("/me/", response_model=UserPublic, name="users:get-current-user")
def get_currently_authenticated_user(current_user: UserInDB = Depends(get_current_user)) -> UserPublic:
    return current_user