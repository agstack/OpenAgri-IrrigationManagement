from fastapi import HTTPException
from pydantic import ValidationError

from .config import settings
from passlib.context import CryptContext

from datetime import datetime, timedelta

import jwt

pwd_context = CryptContext(schemes=["argon2"])


def _create_jwt(
        expiration_time: datetime,
        subject: str
) -> str:
    to_encode = {"exp": expiration_time, "sub": str(subject)}
    jw_token = jwt.encode(payload=to_encode, key=settings.JWT_KEY, algorithm=settings.JWT_ALGORITHM)
    return jw_token


def create_access_token(
        subject: str
) -> str:

    expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRATION_TIME)

    jw_token = _create_jwt(expiration_time=expire, subject=subject)

    return jw_token


def create_refresh_token(
        subject: str
) -> str:

    expire = datetime.now() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRATION_TIME)

    jw_token = _create_jwt(expiration_time=expire, subject=subject)

    return jw_token


def decode_token(
        access_token: str
) -> int:
    try:
        payload = jwt.decode(
            access_token, settings.JWT_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except (jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials",
        )

    return payload["sub"]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)