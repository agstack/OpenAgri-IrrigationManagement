import logging
from typing import Any

import requests
from api import deps
from api.deps import is_not_using_gatekeeper
from core import settings
from crud import user
from fastapi import APIRouter, Depends, HTTPException
from models import User
from requests import RequestException
from schemas import Message, UserCreate, UserMe
from sqlalchemy.orm import Session

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/register/", response_model=Message)
def register(
    user_information: UserCreate, db: Session = Depends(deps.get_db)
) -> Message:
    """
    Registration API for the service.
    """
    logger.info(f"Registration attempt for email: {user_information.email}")
    pwd_check = settings.PASSWORD_SCHEMA_OBJ.validate(pwd=user_information.password)
    if not pwd_check:
        logger.warning(
            f"Registration failed - weak password for email: {user_information.email}"
        )
        raise HTTPException(
            status_code=400,
            detail="Password needs to be at least 8 characters long,"
            "contain at least one uppercase and one lowercase letter, one digit and have no spaces.",
        )

    if settings.USING_GATEKEEPER:
        logger.debug(f"Using GateKeeper for registration: {user_information.email}")
        try:
            response = requests.post(
                url=str(settings.GATEKEEPER_BASE_URL).strip("/") + "/api/register/",
                headers={"Content-Type": "application/json"},
                json={
                    "username": user_information.email,
                    "email": user_information.email,
                    "password": user_information.password,
                },
            )
            logger.debug(
                f"GateKeeper registration response status: {response.status_code}"
            )
        except RequestException as e:
            logger.error(
                f"GateKeeper connection failed during registration for {user_information.email}: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=400, detail="Error, can't connect to gatekeeper instance."
            )

        if response.status_code / 100 != 2:
            logger.error(
                f"GateKeeper registration failed for {user_information.email}. "
                f"Status: {response.status_code}, Response: {response.text}"
            )
            raise HTTPException(
                status_code=400, detail="Error, gatekeeper raise issue with request."
            )
        logger.info(
            f"Successfully registered user via GateKeeper: {user_information.email}"
        )
    else:
        user_db = user.get_by_email(db=db, email=user_information.email)
        if user_db:
            logger.warning(
                f"Registration failed - email already exists: {user_information.email}"
            )
            raise HTTPException(
                status_code=400,
                detail="User with email:{} already exists.".format(
                    user_information.email
                ),
            )

        user.create(db=db, obj_in=user_information)
    response = Message(message="You have successfully registered!")

    return response


@router.get(
    "/me/", response_model=UserMe, dependencies=[Depends(is_not_using_gatekeeper)]
)
def get_me(current_user: User = Depends(deps.get_current_user)) -> Any:
    """
    Returns user email
    """
    logger.debug(f"User profile requested: {current_user.email}")
    return current_user
