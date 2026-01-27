import datetime
from typing import Literal, Optional, List, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api import deps
import crud
from api.deps import get_jwt

from schemas import EToResponse, Calculation, Crop, KcStage
from models import CropKc
from utils import jsonld_eto_response, fetch_parcel_by_id, fetch_parcel_lat_lon, TimeUnit, fetch_weather_data

router = APIRouter()

@router.get("/option-types/", response_model=Dict[str, List[str]], dependencies=[Depends(deps.get_jwt)])
def get_crop_types(
    db: Session = Depends(deps.get_db)
):
    """
    Returns Crop types from DB.
    Used to populate dropdowns in the frontend.
    """

    crops_query = db.query(CropKc.crop).all()
    crops_list = [row[0] for row in crops_query]

    stages_list = [stage.value for stage in KcStage]

    return {
        "crops": crops_list,
        "stages": stages_list
    }


@router.get("/get-calculations/{location_id}/from/{from_date}/to/{to_date}/", dependencies=[Depends(get_jwt)])
def get_calculations(
    location_id: int,
    from_date: datetime.date,
    to_date: datetime.date,
    db: Session = Depends(deps.get_db),
    crop: Optional[Crop] = None,
    stage: Optional[KcStage] = None,
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

    kc_value = None
    if crop and stage:
        kc_row = db.query(CropKc).filter(CropKc.crop == crop.value).first()
        if kc_row is None:
            raise HTTPException(404, f"No KC coefficients found for crop {crop}")

        if stage == KcStage.kc_init:
            kc_value = kc_row.kc_init
        elif stage == KcStage.kc_mid:
            kc_value = kc_row.kc_mid
        elif stage == KcStage.kc_end:
            kc_value = kc_row.kc_end


    eto_response = EToResponse(
            calculations=crud.eto.get_calculations(
                db=db,
                from_date=from_date,
                to_date=to_date,
                location_id=location_id
            )
        )

    if kc_value is not None:
        calculations = eto_response.calculations

        for c in calculations:
            if c.value is not None:
                c.value = c.value * kc_value

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
