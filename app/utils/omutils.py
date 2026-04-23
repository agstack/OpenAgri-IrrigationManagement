import datetime
from datetime import timezone, timedelta
from typing import Optional

import openmeteo_requests
import requests_cache
from retry_requests import retry
from sqlalchemy.orm import Session

import crud
from schemas import EToResponse, Calculation, EtoCreate, Crop, KcStage
from models import CropKc

cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)


def fetch_historical_eto_for_location(
        location_id: int,
        latitude: float,
        longitude: float,
        from_date: datetime.date,
        to_date: datetime.date,
        db: Session,
        crop: Optional[Crop] = None,
        stage: Optional[KcStage] = None,
) -> Optional[EToResponse]:

    kc_value = None
    if crop and stage:
        kc_row = db.query(CropKc).filter(CropKc.crop == crop.value).first()
        if kc_row:
            if stage == KcStage.kc_init:
                kc_value = kc_row.kc_init
            elif stage == KcStage.kc_mid:
                kc_value = kc_row.kc_mid
            elif stage == KcStage.kc_end:
                kc_value = kc_row.kc_end

    existing_db_records = crud.eto.get_calculations(
        db=db,
        from_date=from_date,
        to_date=to_date,
        location_id=location_id
    )
    existing_data_map = {record.date: record.value for record in existing_db_records}

    delta = to_date - from_date
    requested_dates = [from_date + timedelta(days=i) for i in range(delta.days + 1)]
    missing_dates = [d for d in requested_dates if d not in existing_data_map]

    fetched_data_map = {}

    if missing_dates:
        fetch_start = min(missing_dates)
        fetch_end = max(missing_dates)

        url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": fetch_start.strftime("%Y-%m-%d"),
            "end_date": fetch_end.strftime("%Y-%m-%d"),
            "daily": "et0_fao_evapotranspiration",
        }

        try:
            responses = openmeteo.weather_api(url, params=params)
            response = responses[0]

            daily = response.Daily()
            daily_et0 = daily.Variables(0).ValuesAsNumpy()
            start_time = daily.Time()
            interval = daily.Interval()

            new_eto_records = []

            for i, eto_value in enumerate(daily_et0):
                current_time = start_time + (i * interval)
                current_date = datetime.datetime.fromtimestamp(current_time, tz=timezone.utc).date()

                if current_date in missing_dates:
                    py_eto_val = float(eto_value)
                    fetched_data_map[current_date] = py_eto_val

                    new_eto_records.append(
                        EtoCreate(
                            date=current_date,
                            value=py_eto_val,
                            location_id=location_id
                        )
                    )

            if new_eto_records:
                created_records = crud.eto.batch_create(db=db, obj_in=new_eto_records)
                if created_records is None:
                    return None

        except Exception as e:
            return None

    calculations_list = []
    for req_date in requested_dates:
        val = existing_data_map.get(req_date)
        if val is None:
            val = fetched_data_map.get(req_date)

        if val is not None and kc_value is not None:
            val = val * kc_value

        calculations_list.append(Calculation(date=req_date, value=val))

    return EToResponse(calculations=calculations_list)