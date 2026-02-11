import math

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime

from enum import Enum

class WeightScheme(BaseModel):
    val_10: float = Field(..., alias='10')
    val_20: float = Field(..., alias='20')
    val_30: float = Field(..., alias='30')
    val_40: float = Field(..., alias='40')
    val_50: float = Field(..., alias='50')
    val_60: float = Field(..., alias='60')

    @model_validator(mode='after')
    def check_sum_is_one(self) -> "WeightScheme":
        """
        After the individual fields are validated, this function checks if their sum is approximately 1.0.
        """

        all_values = self.__dict__.values()
        total = sum(all_values)

        if not math.isclose(total, 1.0):
            raise ValueError(f"The sum of all values must be 1.0, but it is {total:.8f}")

        return self


class Dataset(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dataset_id: str
    date: datetime
    soil_moisture_10: Optional[float] = 0.0
    soil_moisture_20: Optional[float] = 0.0
    soil_moisture_30: Optional[float] = 0.0
    soil_moisture_40: Optional[float] = 0.0
    soil_moisture_50: Optional[float] = 0.0
    soil_moisture_60: Optional[float] = 0.0
    rain: float
    temperature: float
    humidity: float


class DatasetAnalysis(BaseModel):
    dataset_id: str
    time_period: List[datetime]
    irrigation_events_detected: int
    precipitation_events: int
    high_dose_irrigation_events: int
    high_dose_irrigation_events_dates: List[datetime]
    field_capacity: float
    wilting_point: float
    stress_level: float
    number_of_saturation_days: int
    saturation_dates: List[datetime]
    no_of_stress_days: int
    stress_dates: List[datetime]


class DataPoints(BaseModel):
    date: datetime
    soil_moisture_10: Optional[float] = 0.0
    soil_moisture_20: Optional[float] = 0.0
    soil_moisture_30: Optional[float] = 0.0
    soil_moisture_40: Optional[float] = 0.0
    soil_moisture_50: Optional[float] = 0.0
    soil_moisture_60: Optional[float] = 0.0


class IrrigationDatapoints(BaseModel):
    high_dose_irrigation_days: List[datetime]
    data_points: List[DataPoints]
    field_capacity: float
    wilting_point: float
    stress_level: float


class SoilTypes(str, Enum):
    SAND = "sand"
    LOAMY_SAND = "loamy_sand"
    SANDY_LOAM = "sandy_loam"
    LOAM = "loam"
    SILT_LOAM = "silt_loam"
    SILT = "silt"
    SANDY_CLAY_LOAM = "sandy_clay_loam"
    CLAY_LOAM = "clay_loam"
    SILTY_CLAY_LOAM = "silty_clay_loam"
    SANDY_CLAY = "sandy_clay"
    SILTY_CLAY = "silty_clay"
    CLAY = "clay"
    PEAT = "peat"
    CHALK = "chalk"
