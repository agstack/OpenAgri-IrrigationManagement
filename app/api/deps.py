from typing import Generator

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from core.security import decode_token
from models import User
from crud import user

from core.config import settings
from db.session import SessionLocal
from utils import check_token_for_validity

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/login/access-token/")


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_jwt(
        token: str = Depends(reusable_oauth2),
        db: Session = Depends(get_db)
):
    if not token:
        raise HTTPException(
            status_code=403,
            detail="Not authenticated"
        )

    # If you're using the gatekeeper, check whether the token in question is real
    if settings.USING_GATEKEEPER:
        if not check_token_for_validity(token=token, token_type="access"):
            raise HTTPException(
                status_code=400,
                detail="Error, invalid token"
            )
    else:
        user_id = decode_token(access_token=token)
        user_db = user.get(db=db, id=user_id)
        if not user_db:
            raise HTTPException(
                status_code=400,
                detail="Error, invalid token"
            )

    return token

def get_refresh_token(
        refresh_token: str = None
):
    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    # If you're using the gatekeeper, check whether the token in question is real
    if settings.USING_GATEKEEPER:
        if not check_token_for_validity(token=refresh_token, token_type="refresh"):
            raise HTTPException(
                status_code=400,
                detail="Error, invalid token"
            )

    return refresh_token


# Only use when you're expecting a token that came from PDM, not GK
def get_current_user(
        token: str = Depends(get_jwt),
        db: Session = Depends(get_db)
) -> User:

    user_id = decode_token(token)

    user_db = user.get(db=db, id=user_id)

    if not user_db:
        raise HTTPException(
            status_code=400,
            detail="User ID doesn't exist"
        )

    return user_db


def is_using_gatekeeper():
    if not settings.USING_GATEKEEPER:
        raise HTTPException(
            status_code=400,
            detail="Can't use this API without an instance of a gatekeeper"
        )


def is_not_using_gatekeeper():
    if settings.USING_GATEKEEPER:
        raise HTTPException(
            status_code=400,
            detail="Can't use this API while connected to a gatekeeper"
        )
