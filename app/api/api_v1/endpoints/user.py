from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api import deps
from api.deps import is_not_using_gatekeeper, get_current_user
from models import User
from schemas import Message, UserCreate, UserMe
from crud import user
from core import settings


router = APIRouter()


@router.post("/register/", response_model=Message, dependencies=[Depends(is_not_using_gatekeeper)])
def register(
        user_information: UserCreate,
        db: Session = Depends(deps.get_db)
) -> Message:
    """
    Registration
    """

    pwd_check = settings.PASSWORD_SCHEMA_OBJ.validate(pwd=user_information.password)
    if not pwd_check:
        raise HTTPException(
            status_code=400,
            detail="Password needs to be at least 8 characters long,"
                   "contain at least one uppercase and one lowercase letter, one digit and have no spaces"
        )

    user_db = user.get_by_email(db=db, email=user_information.email)
    if user_db:
        raise HTTPException(
            status_code=400,
            detail="User with email:{} already exists".format(user_information.email)
        )

    user.create(db=db, obj_in=user_information)

    response = Message(
        message="You have successfully registered!"
    )

    return response


@router.get("/me/", response_model=UserMe, dependencies=[Depends(is_not_using_gatekeeper)])
def get_me(
        current_user: User = Depends(get_current_user)
) -> User:
    """
    Returns user information
    """

    return current_user
