import requests
from fastapi import HTTPException
from requests import RequestException

from core import settings


def gatekeeper_logout(
        refresh_token: str
):
    try:
        response = requests.post(
            url=settings.GATEKEEPER_BASE_URL + "/api/logout/",
            json={
                "refresh": "{}".format(refresh_token)
            }
        )
    except RequestException as re:
        raise HTTPException(
            status_code=400,
            detail="Error, can't connect to gatekeeper instance [{}]".format(re)
        )

    if response.status_code == 400:
        raise HTTPException(
            status_code=400,
            detail="Error, missing refresh token"
        )
