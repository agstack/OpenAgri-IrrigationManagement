
import datetime

from typing import List, Literal

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from api import deps
from models import User, Dataset
from schemas import Dataset as DatasetScheme
from schemas import WeightScheme
from schemas import Message
from crud import dataset as crud_dataset
from api.deps import get_jwt

from utils import calculate_soil_analysis_metrics

from utils import jsonld_get_dataset, jsonld_analyse_soil_moisture

from core.config import settings


router = APIRouter()


@router.post("/weights/", response_model=Message, dependencies=[Depends(deps.get_jwt)])
async def set_weights(
        weight_scheme: WeightScheme
):
    """
    Sets the weights for soil analysis.
    """

    new_weights = {
        10: weight_scheme.val_10,
        20: weight_scheme.val_20,
        30: weight_scheme.val_30,
        40: weight_scheme.val_40,
        50: weight_scheme.val_50,
        60: weight_scheme.val_60,
    }

    settings.GLOBAL_WEIGHTS.clear()
    settings.GLOBAL_WEIGHTS.update(new_weights)

    msg = Message(message="Successfully uploaded weights per depths")

    return msg

@router.get("/weights/", response_model=WeightScheme, dependencies=[Depends(deps.get_jwt)])
async def get_weights(

) -> WeightScheme:
    """
    Gets the weights for soil analysis
    """

    weights_for_response = {str(k): v for k, v in settings.GLOBAL_WEIGHTS.items()}

    response_value = WeightScheme.model_validate(weights_for_response)

    return response_value


@router.get("/", dependencies=[Depends(deps.get_jwt)])
def get_all_datasets_ids(
        db: Session = Depends(deps.get_db)
) -> list[str]:
    db_ids = crud_dataset.get_all_datasets(db)
    ids = [row.dataset_id for row in db_ids.all()]
    return ids


@router.post("/", dependencies=[Depends(deps.get_jwt)], response_model=Message)
def upload_dataset(
        dataset: list[DatasetScheme],
        db: Session = Depends(deps.get_db)
):
    try:
        for data in dataset:
            crud_dataset.add_dataset(db, data) # Can be faster!
    except:
        raise HTTPException(status_code=400, detail="Could not upload dataset")

    return Message(message="Successfully uploaded")


@router.get("/{dataset_id}/", dependencies=[Depends(deps.get_jwt)])
async def get_dataset(
        dataset_id: str,
        db: Session = Depends(deps.get_db),
        formatting: Literal["JSON", "JSON-LD"] = "JSON-LD"
):

    db_dataset = crud_dataset.get_datasets(db, dataset_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="No datasets with that id")

    if formatting == "JSON":
        return db_dataset

    return jsonld_get_dataset(db_dataset)


@router.delete("/{dataset_id}/", dependencies=[Depends(deps.get_jwt)], response_model=Message)
def remove_dataset(
        dataset_id: str,
        db: Session = Depends(deps.get_db)
):
    try:
        deleted = crud_dataset.delete_datasets(db, dataset_id)
    except:
        raise HTTPException(status_code=400, detail="Could not delete dataset")

    if deleted == 0:
        raise HTTPException(status_code=400, detail="No dataset with given id")

    return Message(message="Successfully deleted")

@router.get("/{dataset_id}/analysis/", dependencies=[Depends(deps.get_jwt)])
def analyse_soil_moisture(
        dataset_id: str,
        db: Session = Depends(deps.get_db),
        formatting: Literal["JSON", "JSON-LD"] = "JSON-LD"
):
    dataset: list[Dataset] = crud_dataset.get_datasets(db, dataset_id)
    dataset = [DatasetScheme(**data_part.__dict__) for data_part in dataset]

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    result = calculate_soil_analysis_metrics(dataset)

    if formatting == "JSON":
        return result

    return jsonld_analyse_soil_moisture(result)


@router.get("/soil-moisture/{parcel_id}/from/{from_date}/to/{to_date}")
def get_soil_moisture(
        parcel_id: str,
        from_date: datetime.date,
        to_date: datetime.date,
        access_token: str = Depends(get_jwt),
):
    """
        Returns requested soil moisture analysis based on FC farm parcel and date interval
        """
    pass
