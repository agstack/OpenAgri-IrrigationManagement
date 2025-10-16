import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api import deps
import crud
from api.deps import get_jwt

from schemas import EToResponse, Calculation
from utils import jsonld_eto_response, fetch_parcel_by_id, fetch_parcel_lat_lon, TimeUnit, fetch_weather_data

router = APIRouter()


@router.get("/get-calculations/{location_id}/from/{from_date}/to/{to_date}/", dependencies=[Depends(get_jwt)])
def get_calculations(
    location_id: int,
    from_date: datetime.date,
    to_date: datetime.date,
    db: Session = Depends(deps.get_db),
    formatting: Literal["JSON", "JSON-LD"] = "JSON"
):
    """
    Returns ETo calculations for the requested days
    """

    if from_date > to_date:
        raise HTTPException(
            status_code=400,
            detail="Error, from date can't be later than to date"
        )

    location_db = crud.location.get(db=db, id=location_id)

    if location_db is None:
        raise HTTPException(
            status_code=400,
            detail="Error, location with ID:{} does not exist.".format(location_id)
        )

    eto_response = EToResponse(
            calculations=crud.eto.get_calculations(
                db=db,
                from_date=from_date,
                to_date=to_date,
                location_id=location_id
            )
        )

    if formatting.lower() == "json":
        return eto_response
    else:
        jsonld_response = jsonld_eto_response(eto_response)
        return jsonld_response


@router.get("/calculate-gk/")
def calculate_eto_via_gk(
        parcel_id: str,
        from_date: datetime.date,
        to_date: datetime.date,
        access_token: str = Depends(get_jwt),
        formatting: Literal["JSON", "JSON-LD"] = "JSON"
):
    """
    Returns requested ETo calculations based on FC farm parcel and date interval
    """

    if from_date > to_date:
        raise HTTPException(
            status_code=400,
            detail="from_date must be later than to_date, from_date: {} | to_date: {}".format(from_date, to_date)
        )

    parcel_fc = fetch_parcel_by_id(access_token=access_token, parcel_id=parcel_id)

    if not parcel_fc:
        raise HTTPException(
            status_code=400,
            detail="Parcel with ID:{} doesn't exist".format(parcel_id)
        )

    lat, lon = fetch_parcel_lat_lon(parcel_fc)

    weather_data = fetch_weather_data(
        latitude=lat, longitude=lon, access_token=access_token, start_date=from_date, end_date=to_date,
        variables=["et0_fao_evapotranspiration"]
    )

    if not weather_data:
        raise HTTPException(
            status_code=400,
            detail="Error during weather data fetch, none found"
        )

    response_json = EToResponse(
        calculations=[
            Calculation(
                date=wd["date"],
                value=wd["values"]["et0_fao_evapotranspiration"]
            ) for wd in weather_data["data"]
        ]
    )

    if formatting.lower() == "json":
        return response_json
    else:
        jsonld_response = jsonld_eto_response(response_json)
        return jsonld_response
