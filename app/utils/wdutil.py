import datetime

import requests
from fastapi import HTTPException
from requests import RequestException

from core import settings
from enum import Enum

WEATHER_DATA_API_CALL_URL = str(settings.GATEKEEPER_BASE_URL).strip("/") + "/api/proxy/weather_data"

class TimeUnit(Enum):
    HOURLY = "hourly"
    DAILY = "daily"

def fetch_weather_data(
        latitude: float,
        longitude: float,
        start_date: datetime.date,
        end_date: datetime.date,
        variables: list,
        access_token: str,
        radius_km: int = 10,
        how_often: TimeUnit = TimeUnit.DAILY
) -> dict:
    try:
        response = requests.post(
            url=WEATHER_DATA_API_CALL_URL + "/api/v1/history/{}/".format(how_often.value),
            headers={"Content-Type": "application/json", "Authorization": "Bearer {}".format(access_token)},
            json={
                "lat": latitude,
                "lon": longitude,
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "variables": variables,
                "radius_km": radius_km
            }
        )
    except RequestException:
        raise HTTPException(
            status_code=400,
            detail="Error during proxy call via gk"
        )

    if response.status_code == 400:
        raise HTTPException(
            status_code=400,
            detail="Error during weather data api call, original error: {}".format(response.reason)
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=400,
            detail="Error, GK returning 404, Weather Data API missing."
        )

    return response.json()
