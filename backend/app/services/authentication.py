import bcrypt
import jwt

from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.core.config import SECRET_KEY, JWT_ALGORITHM, JWT_AUDIENCE, JWT_TOKEN_PREFIX, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.token import JWTMeta, JWTCreds, JWTPayload
from app.models.user import UserPasswordUpdate, UserInDB

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthException(BaseException):
    pass


class AuthService:
    def create_hashed_password(self, *, plaintext_password: str) -> str:
        hashed_password = self.hash_password(password=plaintext_password)
        return UserPasswordUpdate(password=hashed_password)

    def hash_password(self, *, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, *, password: str, hashed_password: str) -> bool:
        return pwd_context.verify(password, hashed_password)

    def create_access_token_for_user(
            self,
            *,
            user: UserInDB,
            secret_key: str = str(SECRET_KEY),
            audience: str = JWT_AUDIENCE,
            expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES
    ) -> str:
        if not user or not isinstance(user, UserInDB):
            return None

        jwt_meta = JWTMeta(
            aud=audience,
            iat=datetime.timestamp(datetime.utcnow()),
            exp=datetime.timestamp(datetime.utcnow() + timedelta(minutes=expires_in)),
        )

        jwt_creds = JWTCreds(username=user.username)
        token_payload = JWTPayload(
            **jwt_meta.dict(),
            **jwt_creds.dict()
        )

        access_token = jwt.encode(token_payload.dict(), secret_key, algorithm=JWT_ALGORITHM)
        return access_token

    def get_username_from_token(self, *, token: str, secret_key: str) -> Optional[str]:
        try:
            decoded_token = jwt.decode(token, str(secret_key), audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM])
            payload = JWTPayload(**decoded_token)
        except (jwt.PyJWTError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate token credentials.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return payload.username
