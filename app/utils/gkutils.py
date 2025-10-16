import requests
from fastapi import HTTPException
from requests import RequestException

from core import settings


def gatekeeper_logout(
        refresh_token: str
):
    try:
        response = requests.post(
            url=str(settings.GATEKEEPER_BASE_URL).strip("/") + "/api/logout/",
            headers={"Content-Type": "application/json"},
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

    if response.status_code == 500:
        raise HTTPException(
            status_code=400,
            detail="Error, gatekeeper returned a 500!"
        )

def check_token_for_validity(
        token: str,
        token_type: str
):
    try:
        response = requests.post(
            url=str(settings.GATEKEEPER_BASE_URL).strip("/") + "/api/validate_token/",
            headers={"Content-Type": "application/json"},
            json={
                "token": token,
                "token_type": token_type # Can be either access or refresh
            }
        )
    except RequestException as re:
        raise HTTPException(
            status_code=400,
            detail="Error, can't connect to gatekeeper instance [{}]".format(re)
        )

    if response.status_code == 400:

        response_json = response.json()

        if "error" in response_json:
            error_message = response_json["error"]

            if error_message == "Token is required":
                raise HTTPException(
                    status_code=400,
                    detail="Error, missing token"
                )
        return False

    if response.status_code == 500:
        raise HTTPException(
            status_code=400,
            detail="Error, gatekeeper returned a 500"
        )

    return True
