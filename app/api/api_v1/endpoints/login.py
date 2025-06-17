from typing import Annotated

import requests

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from requests import RequestException
from sqlalchemy.orm import Session

from api.deps import get_jwt
from core.security import create_access_token, create_refresh_token
from core.config import settings
from api import deps
from crud import user
from schemas import Token, Message
from utils import gatekeeper_logout

router = APIRouter()


@router.post("/access-token/", response_model=Token)
def login_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Session = Depends(deps.get_db)
) -> Token:
    """
    OAuth2 compatible token login, get an [access token, refresh token] pair for future requests
    """

    if not settings.USING_GATEKEEPER:

        user_db = user.authenticate(
            db=db,
            email=form_data.username,
            password=form_data.password
        )

        if not user_db:
            raise HTTPException(
                status_code=400,
                detail="Incorrect email or password"
            )

        response_token = Token(
            access_token=create_access_token(user_db.id),
            refresh_token=create_refresh_token(user_db.id),
            token_type="bearer"
        )
    else:
        try:
            response = requests.post(
                url=settings.GATEKEEPER_BASE_URL.unicode_string() + "api/login/",
                headers={"Content-Type": "application/json"},
                json={"username": "{}".format(form_data.username), "password": "{}".format(form_data.password)}
            )
        except RequestException:
            raise HTTPException(
                status_code=400,
                detail="Network error during communication with GateKeeper, please try again"
            )

        if response.status_code == 401:
            raise HTTPException(
                status_code=400,
                detail="Error, no active account found with these credentials"
            )

        if response.status_code == 400:
            raise HTTPException(
                status_code=400,
                detail="Error, missing username/password values, please enter your username and/or password"
            )

        response_json = response.json()

        if "success" in response_json:
            response_token = Token(
                access_token=response.json()["access"],
                refresh_token=response.json()["refresh"],
                token_type="bearer"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Error, unsuccessfully login attempt, GateKeeper returned 200 with success==False"
            )

    return response_token


@router.post("/logout/", response_model=Message, dependencies=[Depends(deps.is_using_gatekeeper)])
def logout(
        token: Token = Depends(get_jwt)
) -> Message:
    """
    Logout
    """

    gatekeeper_logout(token.refresh_token)

    response_message = Message(
        message="Successfully logged out!"
    )

    return response_message
