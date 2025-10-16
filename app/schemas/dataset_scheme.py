import math

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import List
from datetime import datetime

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
    soil_moisture_10: float
    soil_moisture_20: float
    soil_moisture_30: float
    soil_moisture_40: float
    soil_moisture_50: float
    soil_moisture_60: float
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
    stress_level: float
    number_of_saturation_days: int
    saturation_dates: List[datetime]
    no_of_stress_days: int
    stress_dates: List[datetime]
