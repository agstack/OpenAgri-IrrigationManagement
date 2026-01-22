import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from enum import Enum

class Crop(str, Enum):
    sugar_beets = "SUGAR_BEETS"
    potatoes = "POTATOES"


class KcStage(str, Enum):
    kc_init = "KC_INIT"
    kc_mid = "KC_MID"
    kc_end = "KC_END"


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
