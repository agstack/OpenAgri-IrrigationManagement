import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class Calculation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: datetime.date
    value: Optional[float]


class EToResponse(BaseModel):
    calculations: List[Calculation]



class EToInputData(BaseModel):
    t_min: float
    t_max: float
    t_mean: float
    rh_mean: float
    u_z: float
    p: float

    sea_level: int


class EtoCreate(BaseModel):
    date: datetime.date
    value: float

    location_id: int


class EtoUpdate(BaseModel):
    pass
