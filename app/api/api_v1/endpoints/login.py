import logging
from typing import Annotated

import requests
from api import deps
from core.config import settings
from core.security import *
from crud import user
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from requests import RequestException
from schemas import Message, Token
from sqlalchemy.orm import Session
from utils import gatekeeper_logout

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/access-token/", response_model=Token)
def login_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(deps.get_db),
) -> Token:
    """
    OAuth2 compatible token login, get an [access token, refresh token] pair for future requests
    """
    logger.info(f"Login attempt for user: {form_data.username}")
    if not settings.USING_GATEKEEPER:
        user_db = user.authenticate(
            db=db, email=form_data.username, password=form_data.password
        )

        if not user_db:
            logger.warning(
                f"Failed login attempt - Invalid credentials for user: {form_data.username}"
            )
            raise HTTPException(status_code=400, detail="Incorrect email or password")
        logger.info(f"Successful login for user: {form_data.username}")
        response_token = Token(
            access_token=create_token(
                user_db.id, settings.ACCESS_TOKEN_EXPIRATION_TIME
            ),
            refresh_token=create_token(
                user_db.id, settings.REFRESH_TOKEN_EXPIRATION_TIME
            ),
            token_type="bearer",
        )
    else:
        try:
            logger.debug(f"Attempting GateKeeper login for user: {form_data.username}")
            response = requests.post(
                url=str(settings.GATEKEEPER_BASE_URL).rstrip("/") + "/api/login/",
                headers={"Content-Type": "application/json"},
                json={
                    "username": "{}".format(form_data.username),
                    "password": "{}".format(form_data.password),
                },
            )
            logger.debug(f"GateKeeper response status: {response.status_code}")
        except RequestException as e:
            logger.error(
                f"GateKeeper login request failed for user {form_data.username}: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=400,
                detail="Network error during communication with GateKeeper, please try again",
            )

        if response.status_code == 401:
            logger.warning(
                f"GateKeeper authentication failed (401) for user: {form_data.username}"
            )
            raise HTTPException(
                status_code=400,
                detail="Error, no active account found with these credentials",
            )

        if response.status_code == 400:
            logger.warning(
                "Gatekeeper rejected login credentials for user: %s", form_data.username
            )
            raise HTTPException(
                status_code=400,
                detail="Error, missing username/password values, please enter your username and/or password",
            )

        response_json = response.json()

        if response_json["success"]:
            logger.info(f"Successful GateKeeper login for user: {form_data.username}")
            response_token = Token(
                access_token=response.json()["access"],
                refresh_token=response.json()["refresh"],
                token_type="bearer",
            )
        else:
            logger.error(
                f"GateKeeper returned success=False for user: {form_data.username}. Response: {response_json}"
            )
            raise HTTPException(
                status_code=400,
                detail="Error, unsuccessful login attempt, GateKeeper returned 200 with success==False",
            )

    return response_token


@router.post(
    "/logout/",
    response_model=Message,
    dependencies=[Depends(deps.is_using_gatekeeper), Depends(deps.get_jwt)],
)
def logout(refresh_token: str = Depends(deps.get_refresh_token)) -> Message:
    """
    Logout
    """
    logger.info("User logging out, invalidating refresh token")
    gatekeeper_logout(refresh_token)
    logger.info("User successfully logged out")
    response_message = Message(message="Successfully logged out!")

    return response_message
