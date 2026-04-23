from typing import List, Dict, Union, Tuple, Optional

from schemas import Dataset as DatasetScheme
from schemas import DatasetAnalysis, IrrigationDatapoints, DataPoints, SoilTypes

from datetime import datetime

from core import settings

from typing import cast

import pandas as pd
import numpy as np

import re

_SM_PATTERN = re.compile(r'(?i)soil.?moisture.?(\d+)', re.IGNORECASE)

_NUMBERED_DEPTH_MAP = {1: 10, 2: 30, 3: 40, 4: 50, 5: 20, 6: 60}

def _extract_sm_cols(df: pd.DataFrame) -> Dict[int, str]:
    """
    Return {depth_int: column_name} for every soil moisture column in df,
    regardless of the naming convention used by model_dump().

    Matches all of: soil_moisture_10, soilMoisture10, Soil_Moisture_10,
                    soil_moisture_10cm, Soil Moisture 10cm (%), ...
    """
    result = {}
    for col in df.columns:
        m = _SM_PATTERN.search(str(col))
        if m:
            raw_num = int(m.group(1))
            if raw_num in _NUMBERED_DEPTH_MAP and raw_num <= 6:
                depth = _NUMBERED_DEPTH_MAP[raw_num]
            else:
                depth = raw_num
            result[depth] = col

    return result


def _replace_zero_sm_with_nan(df: pd.DataFrame) -> pd.DataFrame:
    sm_cols = _extract_sm_cols(df)
    for col in sm_cols.values():
        df[col] = df[col].replace(0.0, np.nan)

    return df


def _is_cumulative_rain(rain_series: pd.Series,
                        cumulative_threshold: float = 0.90) -> bool:
    """
    Auto-detect whether the rain column is a cumulative tipping-bucket counter.

    A cumulative counter broadcasts the same value repeatedly between tips.
    If >= `cumulative_threshold` fraction of non-zero readings have diff == 0
    the series is considered cumulative.
    """
    nonzero = rain_series[rain_series > 0]
    if nonzero.empty:
        return False
    zero_diffs = (rain_series.diff()[rain_series > 0] == 0).sum()
    return (zero_diffs / len(nonzero)) >= cumulative_threshold


def decode_tipping_bucket_rain(rain_series: pd.Series) -> pd.Series:
    """
    Convert a cumulative tipping-bucket counter into per-interval increments.
    """
    increments = rain_series.diff().clip(lower=0)
    increments.iloc[0] = 0
    return increments


def preprocess_dataset(data: List[DatasetScheme]) -> pd.DataFrame:
    """Standard preprocessing: convert to DataFrame, set timestamp index, fill missing rain."""
    data_dict = [item.model_dump() for item in data]
    df = pd.DataFrame(data_dict)

    df.rename(columns={'date': 'timestamp'}, inplace=True)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)

    df.sort_index(inplace=True)
    df = df[~df.index.duplicated(keep='last')]

    df = _replace_zero_sm_with_nan(df)

    df['rain'] = df['rain'].fillna(0)

    if _is_cumulative_rain(df['rain']):
        print("Rain column detected as cumulative tipping-bucket — decoding to increments.")
        df['rain'] = decode_tipping_bucket_rain(df['rain'])
    else:
        print("Rain column detected as per-interval increments — no decoding needed.")

    return df


def weighted_average(values: List[Tuple[int, float]], weights: Dict[int, float]) -> Optional[float]:
    """
    Compute weighted average across depths given [(depth, value), ...].
    """
    total, weight_sum = 0.0, 0.0
    for depth, val in values:
        if depth in weights and val is not None and pd.notna(val):
            total += weights[depth] * val
            weight_sum += weights[depth]
    return round(total / weight_sum, 4) if weight_sum else None


def _log_active_depths(sm_cols: Dict[int, str], df: pd.DataFrame) -> None:
    active = [col for col in sm_cols.values() if df[col].notna().any()]
    missing = [col for col in sm_cols.values() if not df[col].notna().any()]
    print(f"Active soil moisture depths : {active}")
    if missing:
        print(f"Depths with no data (all NaN): {missing} - excluded from calculations")


def calculate_field_capacity(
    df: pd.DataFrame,
    rain_threshold_mm=settings.RAIN_THRESHOLD_MM,
    time_window_hours=settings.FIELD_CAPACITY_WINDOW_HOURS,
    rain_zero_tolerance=settings.RAIN_ZERO_TOLERANCE
) -> Union[float, None]:
    """Calculates weighted field capacity using daily rain totals."""

    sm_cols = _extract_sm_cols(df)
    if not sm_cols:
        print("WARNING: No soil moisture columns detected. Check schema field names.")
        return None

    _log_active_depths(sm_cols, df)

    # Fill within-depth gaps; all-NaN columns remain all-NaN (skipped later)
    for col in sm_cols.values():
        df[col] = df[col].ffill().bfill()

    temp_df = df[['rain']].copy()
    temp_df['is_raining'] = temp_df['rain'] > rain_zero_tolerance
    temp_df['rain_group'] = (temp_df['is_raining'] != temp_df['is_raining'].shift()).cumsum()

    rain_events = temp_df[temp_df['is_raining']].groupby('rain_group')

    field_capacity_candidates: Dict[str, List[float]] = {col: [] for col in sm_cols.values()}

    for _, event in rain_events:
        total_rain = event['rain'].sum()
        if total_rain < rain_threshold_mm:
            continue

        end_of_rain = event.index[-1]
        search_period = df.loc[end_of_rain: end_of_rain + pd.Timedelta(hours=time_window_hours)]

        if search_period.empty:
            continue

        for col in sm_cols.values():
            # dropna() ensures NaN from all-NaN columns never enters candidates
            valid = search_period[col].dropna()
            if not valid.empty:
                field_capacity_candidates[col].append(float(valid.max()))

    if not any(field_capacity_candidates.values()):
        print(
            "WARNING: No qualifying rain events found for field capacity calculation. "
            f"Current RAIN_THRESHOLD_MM={rain_threshold_mm}. Consider lowering it."
        )
        return None

    final_field_capacity = {
        depth: (float(np.median(field_capacity_candidates[col])) / 100)
        if field_capacity_candidates[col] else None
        for depth, col in sm_cols.items()
    }

    fc_list: List[Tuple[int, float]] = [
        (depth, cast(float, val))
        for depth, val in final_field_capacity.items()
        if val is not None and pd.notna(val)
    ]

    return weighted_average(fc_list, settings.GLOBAL_WEIGHTS)


def detect_weighted_moisture(df: pd.DataFrame) -> pd.Series:
    """Compute vectorized weighted soil moisture across all timestamps."""
    sm_cols = _extract_sm_cols(df)
    valid_depths = [
        depth for depth, col in sm_cols.items()
        if depth in settings.GLOBAL_WEIGHTS and df[col].notna().any()
    ]
    if not valid_depths:
        return pd.Series([], dtype=float)

    weights = np.array([settings.GLOBAL_WEIGHTS[d] for d in valid_depths])
    soil_cols = [sm_cols[d] for d in valid_depths]

    moisture_values = df[soil_cols].div(100)
    weighted_sum = moisture_values.mul(weights, axis=1).sum(axis=1)
    weighted_avg = weighted_sum / weights.sum()  # normalize to present depths only
    return weighted_avg


def detect_irrigation_from_sm_resposne(
        df: pd.DataFrame,
        daily_rain: pd.Series,
        high_dose_threshold_mm: float,
        sm_jump_pct: float = settings.SM_IRRIGATION_JUMP_PCT,
        gauge_blackout_days: int = settings.SM_GAUGE_BLACKOUT_DAYS,
) -> pd.Series:

    weighted_moisture = detect_weighted_moisture(df)
    if weighted_moisture.empty:
        return pd.Series(dtype=float)

    daily_sm = (weighted_moisture * 100).resample('1D').mean()
    daily_sm_rise = daily_sm.diff()

    sm_jump_days = daily_sm_rise[daily_sm_rise >= sm_jump_pct].index

    gauge_high_days = daily_rain[daily_rain >= high_dose_threshold_mm].index
    blackout: set = set()
    for d in gauge_high_days:
        for offset in range(gauge_blackout_days + 1):
            blackout.add((d + pd.Timedelta(days=offset)).normalize())

    missed_days = sm_jump_days[~sm_jump_days.isin(blackout)]
    return daily_sm_rise.loc[missed_days]


def detect_weighted_stress_days(df: pd.DataFrame, weighted_fc: float,
                                stress_threshold_fraction=settings.STRESS_THRESHOLD_FRACTION) -> List[datetime]:
    """Vectorized detection of stress days."""
    if not weighted_fc:
        return []
    weighted_moisture = detect_weighted_moisture(df)
    stress_threshold = weighted_fc * stress_threshold_fraction
    return weighted_moisture[weighted_moisture < stress_threshold].index.tolist()


def detect_weighted_oversaturation(df: pd.DataFrame, weighted_fc: float) -> List[datetime]:
    """Vectorized detection of oversaturation days."""
    if not weighted_fc:
        return []
    weighted_moisture = detect_weighted_moisture(df)
    return weighted_moisture[weighted_moisture > weighted_fc].index.tolist()


def suggest_wilting_point_fraction(df: pd.DataFrame,
                                   field_capacity: float,
                                   baseline_wp_fraction: float = 0.5) -> float:
    if field_capacity is None or field_capacity == 0:
        return baseline_wp_fraction

    weighted_moisture = detect_weighted_moisture(df)
    if weighted_moisture.empty:
        return baseline_wp_fraction

    historical_min = weighted_moisture.quantile(0.01)
    observed_min_fraction = historical_min / field_capacity

    if observed_min_fraction < baseline_wp_fraction:
        suggested_wp = max(0.1, observed_min_fraction - 0.05)
        return round(suggested_wp, 2)

    return baseline_wp_fraction


def suggest_stress_threshold_fraction(df: pd.DataFrame,
                                      field_capacity: float,
                                      wilting_point_fraction: float) -> float:
    """Auto-tune stress threshold, always strictly above the wilting point."""
    if field_capacity is None or field_capacity == 0:
        return 0.5

    weighted_moisture = detect_weighted_moisture(df)
    if weighted_moisture.empty:
        return 0.5

    driest_p05 = weighted_moisture.quantile(0.05)
    suggested_fraction = driest_p05 / field_capacity

    min_safe_fraction = wilting_point_fraction + 0.05
    suggested_fraction = max(min_safe_fraction, min(0.85, suggested_fraction))

    return round(suggested_fraction + 0.02, 2)


def calculate_soil_analysis_metrics(dataset: List[DatasetScheme],
                                    field_capacity: Optional[float] = None,
                                    wilting_point: Optional[float] = None) -> DatasetAnalysis:
    df = preprocess_dataset(dataset)

    start_date = df.index.min().isoformat()
    end_date = df.index.max().isoformat()

    daily_rain = df['rain'].resample("1D").sum()

    irrigation_series = daily_rain[
        (daily_rain > 0) & (daily_rain < settings.LOW_DOSE_THRESHOLD_MM)
        ]
    irrigation_events_detected = irrigation_series.count()
    irrigation_events_dates = [d.isoformat() for d in irrigation_series.index]

    precipitation_series = daily_rain[daily_rain > 0]
    precipitation_events = precipitation_series.count()
    precipitation_events_dates = [d.isoformat() for d in precipitation_series.index]

    gauge_high_dose = daily_rain[daily_rain >= settings.HIGH_DOSE_THRESHOLD_MM]
    sm_detected = detect_irrigation_from_sm_resposne(
        df,
        daily_rain,
        high_dose_threshold_mm=settings.HIGH_DOSE_THRESHOLD_MM,
        sm_jump_pct=settings.SM_IRRIGATION_JUMP_PCT,
        gauge_blackout_days=settings.SM_GAUGE_BLACKOUT_DAYS
    )

    all_high_dose_dates = sorted(gauge_high_dose.index.union(sm_detected.index))
    high_dose_irrigation_events = len(all_high_dose_dates)
    high_dose_irrigation_events_dates = [d.isoformat() for d in all_high_dose_dates]


    calculated_fc = calculate_field_capacity(df)

    weighted_fc = 0.0
    stress_level = 0.0
    wilting_point_val = 0.0
    stress_threshold_fraction = settings.STRESS_THRESHOLD_FRACTION

    if calculated_fc is not None:
        weighted_fc = calculated_fc
    elif field_capacity is not None:
        weighted_fc = field_capacity

    if weighted_fc > 0:
        if wilting_point is not None and wilting_point > 0:
            baseline_wp_fraction = wilting_point / weighted_fc
        else:
            baseline_wp_fraction = 0.5

        wp_fraction = suggest_wilting_point_fraction(df, weighted_fc, baseline_wp_fraction)
        wilting_point_val = weighted_fc * wp_fraction

        stress_threshold_fraction = suggest_stress_threshold_fraction(df, weighted_fc, wp_fraction)
        stress_level = weighted_fc * stress_threshold_fraction

    oversaturation_dates = detect_weighted_oversaturation(df, weighted_fc)
    stress_dates = detect_weighted_stress_days(df, weighted_fc, stress_threshold_fraction)

    distinct_saturation_dates = sorted({
        datetime(d.year, d.month, d.day) for d in oversaturation_dates
    })
    distinct_stress_dates = sorted({
        datetime(d.year, d.month, d.day) for d in stress_dates
    })

    return DatasetAnalysis(
        dataset_id=getattr(dataset[0], "dataset_id", "unknown") if dataset else "unknown",
        time_period=[start_date, end_date],
        irrigation_events_detected=irrigation_events_detected,
        irrigation_events_dates=irrigation_events_dates,
        precipitation_events=precipitation_events,
        precipitation_events_dates=precipitation_events_dates,
        high_dose_irrigation_events=high_dose_irrigation_events,
        high_dose_irrigation_events_dates=high_dose_irrigation_events_dates,
        field_capacity=weighted_fc if weighted_fc is not None else 0.0,
        wilting_point=round(wilting_point_val, 4),
        stress_level=round(stress_level, 4),
        number_of_saturation_days=len(distinct_saturation_dates),
        saturation_dates=distinct_saturation_dates,
        no_of_stress_days=len(distinct_stress_dates),
        stress_dates=distinct_stress_dates,
    )


def calculate_irrigation_datapoints(dataset: List[DatasetScheme],
                                    field_capacity: Optional[float] = None,
                                    wilting_point: Optional[float] = None) -> IrrigationDatapoints:
    df = preprocess_dataset(dataset)

    daily_rain = df['rain'].resample("1D").sum()

    gauge_high_dose = daily_rain[daily_rain >= settings.HIGH_DOSE_THRESHOLD_MM]
    sm_detected = detect_irrigation_from_sm_resposne(
        df,
        daily_rain,
        high_dose_threshold_mm=settings.HIGH_DOSE_THRESHOLD_MM,
        sm_jump_pct=settings.SM_IRRIGATION_JUMP_PCT,
        gauge_blackout_days=settings.SM_GAUGE_BLACKOUT_DAYS
    )

    all_high_dose_dates = sorted(gauge_high_dose.index.union(sm_detected.index))
    high_dose_irrigation_events_dates = [d.isoformat() for d in all_high_dose_dates]

    all_soil_cols = [
        'soil_moisture_10', 'soil_moisture_20', 'soil_moisture_30',
        'soil_moisture_40', 'soil_moisture_50', 'soil_moisture_60'
    ]

    available_soil_cols = [col for col in all_soil_cols if col in df.columns]

    df_data_points = df[available_soil_cols].reset_index().rename(columns={'timestamp': 'date'})

    df_data_points.replace({np.nan: None}, inplace=True)
    data_records = df_data_points.to_dict('records')

    data_points_list = [DataPoints(**record) for record in data_records]

    calculated_fc = calculate_field_capacity(df)

    weighted_fc = 0.0
    stress_level = 0.0
    wilting_point_val = 0.0
    stress_threshold_fraction = settings.STRESS_THRESHOLD_FRACTION

    if calculated_fc is not None:
        weighted_fc = calculated_fc
    elif field_capacity is not None:
        weighted_fc = field_capacity

    if weighted_fc > 0:
        if wilting_point is not None and wilting_point > 0:
            baseline_wp_fraction = wilting_point / weighted_fc
        else:
            baseline_wp_fraction = 0.5

        wp_fraction = suggest_wilting_point_fraction(df, weighted_fc, baseline_wp_fraction)
        wilting_point_val = weighted_fc * wp_fraction

        stress_threshold_fraction = suggest_stress_threshold_fraction(df, weighted_fc, wp_fraction)
        stress_level = weighted_fc * stress_threshold_fraction

    return IrrigationDatapoints(
        high_dose_irrigation_days=high_dose_irrigation_events_dates,
        data_points=data_points_list,
        field_capacity=weighted_fc if weighted_fc is not None else 0.0,
        wilting_point=round(wilting_point_val, 4),
        stress_level=round(stress_level, 4)
    )