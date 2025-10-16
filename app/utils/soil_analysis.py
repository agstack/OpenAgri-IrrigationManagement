from typing import List, Dict, Union, Tuple

from schemas import Dataset as DatasetScheme
from schemas import DatasetAnalysis

from datetime import datetime

from core import settings

import pandas as pd
import numpy as np


def preprocess_dataset(data: List[DatasetScheme]) -> pd.DataFrame:
    """Standard preprocessing: convert to DataFrame, set timestamp index, fill missing rain."""
    data_dict = [item.model_dump() for item in data]
    df = pd.DataFrame(data_dict)
    df.rename(columns={'date': 'timestamp'}, inplace=True)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    df['rain'] = df['rain'].fillna(0)
    return df



def weighted_average(values: List[Tuple[int, float]], weights: Dict[int, float]) -> float | None:
    """Compute weighted average across depths given [[depth, value], ...]."""
    total, weight_sum = 0.0, 0.0
    for depth, val in values:
        if depth in weights and val is not None:
            total += weights[depth] * val
            weight_sum += weights[depth]
    return round(total / weight_sum, 4) if weight_sum else None



def calculate_field_capacity(
    df: pd.DataFrame,
    rain_threshold_mm=settings.RAIN_THRESHOLD_MM,
    time_window_hours=settings.FIELD_CAPACITY_WINDOW_HOURS,
    rain_zero_tolerance=settings.RAIN_ZERO_TOLERANCE
) -> Union[float, None]:
    """Calculates weighted field capacity using daily rain totals."""

    # --- Identify soil moisture columns ---
    soil_moisture_cols = {int(col.split('_')[2]): col for col in df.columns if 'soil_moisture' in col}
    print("Detected soil moisture columns:", soil_moisture_cols)

    # Fill missing values
    for col in soil_moisture_cols.values():
        df[col] = df[col].ffill().bfill()

    # --- Aggregate rain to daily totals ---
    daily_rain = df['rain'].resample("1D").sum()
    major_rain_days = daily_rain[daily_rain >= rain_threshold_mm].index
    print("Number of major rain days:", len(major_rain_days))

    if len(major_rain_days) == 0:
        return None

    field_capacity_candidates = {col: [] for col in soil_moisture_cols.values()}

    # --- For each rain day, find post-rain window and max moisture ---
    for rain_day in major_rain_days:
        # End of rain = first dry hour after rain day
        day_slice = df.loc[rain_day: rain_day + pd.Timedelta("1D")]
        end_of_rain_candidates = day_slice[day_slice['rain'] < rain_zero_tolerance].index
        if len(end_of_rain_candidates) > 0:
            end_of_rain = end_of_rain_candidates[0]
        elif not day_slice.empty:
            end_of_rain = day_slice.index[-1]
        else:
            continue  # skip this event if no data

        # Look forward a window of hours after end of rain
        search_period = df.loc[end_of_rain: end_of_rain + pd.Timedelta(hours=time_window_hours)]
        print(f"Search period for rain day {rain_day.date()}: {len(search_period)} rows")

        for col in soil_moisture_cols.values():
            if not search_period.empty and not search_period[col].isnull().all():
                fc_candidate = search_period[col].max()
                field_capacity_candidates[col].append(fc_candidate)

    # --- Median across candidates, convert to fraction ---
    final_field_capacity = {
        depth: (float(np.median(field_capacity_candidates[col])) / 100)
        if len(field_capacity_candidates[col]) > 0 else None
        for depth, col in soil_moisture_cols.items()
    }

    # Weighted average flattening
    fc_list = [(depth, float(val)) for depth, val in final_field_capacity.items() if val is not None]
    return weighted_average(fc_list, settings.GLOBAL_WEIGHTS)


def detect_weighted_moisture(df: pd.DataFrame) -> pd.Series:
    """Compute vectorized weighted soil moisture across all timestamps."""
    valid_depths = [depth for depth in settings.GLOBAL_WEIGHTS if f"soil_moisture_{depth}" in df.columns]
    if not valid_depths:
        return pd.Series([], dtype=float)

    weights = np.array([settings.GLOBAL_WEIGHTS[d] for d in valid_depths])
    soil_cols = [f"soil_moisture_{d}" for d in valid_depths]

    # Normalize soil moisture to fraction
    moisture_values = df[soil_cols].div(100)
    weighted_sum = moisture_values.mul(weights, axis=1).sum(axis=1)
    weighted_avg = weighted_sum / weights.sum()
    return weighted_avg


def detect_weighted_stress_days(df: pd.DataFrame, weighted_fc: float,
                                stress_threshold_fraction=settings.STRESS_THRESHOLD_FRACTION) -> List[datetime]:
    """Vectorized detection of stress days."""
    if weighted_fc is None:
        return []
    weighted_moisture = detect_weighted_moisture(df)
    stress_threshold = weighted_fc * stress_threshold_fraction
    return weighted_moisture[weighted_moisture < stress_threshold].index.tolist()


def detect_weighted_oversaturation(df: pd.DataFrame, weighted_fc: float) -> List[datetime]:
    """Vectorized detection of oversaturation days."""
    if weighted_fc is None:
        return []
    weighted_moisture = detect_weighted_moisture(df)
    return weighted_moisture[weighted_moisture > weighted_fc].index.tolist()



def calculate_soil_analysis_metrics(dataset: List[DatasetScheme]) -> DatasetAnalysis:
    df = preprocess_dataset(dataset)

    # 1. Time period
    start_date, end_date = df.index.min().isoformat(), df.index.max().isoformat()

    # --- Resample rain to daily totals ---
    daily_rain = df['rain'].resample("1D").sum()

    # 2. Irrigation/precipitation events (daily totals)
    irrigation_events_detected = (daily_rain[(daily_rain > 0) & (daily_rain < settings.LOW_DOSE_THRESHOLD_MM)]).count()
    precipitation_events = (daily_rain[daily_rain > 0]).count()
    high_dose_irrigation = daily_rain[daily_rain >= settings.HIGH_DOSE_THRESHOLD_MM]

    high_dose_irrigation_events = high_dose_irrigation.count()
    high_dose_irrigation_events_dates = [d.isoformat() for d in high_dose_irrigation.index]

    # 3. Field capacity (weighted, based on daily rain)
    weighted_fc = calculate_field_capacity(df)

    # 4. Stress and oversaturation detection
    stress_threshold_fraction = settings.STRESS_THRESHOLD_FRACTION
    oversaturation_dates = detect_weighted_oversaturation(df, weighted_fc)
    stress_dates = detect_weighted_stress_days(df, weighted_fc, stress_threshold_fraction)

    # Use sets to ensure distinct dates before sorting
    distinct_saturation_dates = sorted({d.date().isoformat() for d in oversaturation_dates})
    distinct_stress_dates = sorted({d.date().isoformat() for d in stress_dates})

    # 5. Format results
    return DatasetAnalysis(
        dataset_id=getattr(dataset[0], "dataset_id", "unknown") if dataset else "unknown",
        time_period=[start_date, end_date],
        irrigation_events_detected=irrigation_events_detected,
        precipitation_events=precipitation_events,
        high_dose_irrigation_events=high_dose_irrigation_events,
        high_dose_irrigation_events_dates=high_dose_irrigation_events_dates,
        field_capacity=weighted_fc if weighted_fc is not None else 0.0,
        stress_level=round(weighted_fc * stress_threshold_fraction, 4) if weighted_fc is not None else 0.0,
        number_of_saturation_days=len(distinct_saturation_dates),
        saturation_dates=distinct_saturation_dates,
        no_of_stress_days=len(distinct_stress_dates),
        stress_dates=distinct_stress_dates,
    )
