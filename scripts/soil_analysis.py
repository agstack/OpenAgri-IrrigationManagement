#!/usr/bin/env python3
import argparse
import json
import re
import sys
from typing import List, Dict, Any, Optional

import pandas as pd
import requests
import matplotlib.pyplot as plt

# ======================
# Config / constants
# ======================
TARGET_DEPTHS = [10, 20, 30, 40, 50, 60]

# ======================
# Utilities
# ======================
def isoformat_utc(val) -> Optional[str]:
    """Parse with pandas only; return ISO-8601 in UTC with 'Z'. Returns None on failure/NaT."""
    if pd.isna(val):
        return None
    ts = pd.to_datetime(val, utc=True, errors="coerce")
    if ts is pd.NaT:
        return None
    # pandas may return numpy datetime64; convert to python datetime first
    ts = pd.Timestamp(ts).to_pydatetime()
    return ts.isoformat().replace("+00:00", "Z")


# --- CSV Parsing ---
# Read the CSV file into a list of dictionaries (rows).
# Detect required columns: date, rain, temperature, humidity.
# Detect soil moisture depth columns (e.g. "Soil Moisture 30cm").
# Add missing soil moisture depths as new columns with zeros.
def find_date_column(df: pd.DataFrame) -> str:
    for c in df.columns:
        cl = c.lower()
        if cl in {"date", "datetime", "timestamp", "time"} or "date" in cl or "timestamp" in cl:
            return c
    raise ValueError("Could not find a date/timestamp column (e.g., 'date', 'timestamp').")

def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip()).lower()

def detect_rain_col(df: pd.DataFrame) -> str:
    for c in df.columns:
        cl = normalize(c)
        if re.search(r'\brain\b', cl):
            return c
    for c in df.columns:
        cl = normalize(c)
        if "precip" in cl or "rainfall" in cl:
            return c
    raise ValueError("Missing required rainfall column (expected 'rain', 'precipitation', etc.).")

def detect_temp_col(df: pd.DataFrame) -> str:
    for c in df.columns:
        cl = normalize(c)
        if re.search(r'\btemperature\b', cl) or re.search(r'\btemp\b', cl):
            return c
    raise ValueError("Missing required temperature column (expected 'temperature' or 'temp').")

def detect_humidity_col(df: pd.DataFrame) -> str:
    for c in df.columns:
        cl = normalize(c)
        if "humidity" in cl or re.search(r'\brh\b', cl):
            return c
    raise ValueError("Missing required humidity column (expected 'humidity' or 'RH').")

def parse_depth_from_header(col: str) -> Optional[int]:
    cl = col.lower()
    # soil_moisture_30 or "Soil Moisture 30"
    m = re.search(r'soil[_\s]*moisture[_\s]*([0-9]{1,3})\b', cl)
    if m: return int(m.group(1))
    # with cm, e.g. "Soil Moisture 30cm (%)"
    m = re.search(r'soil[\s_]*moisture.*?([0-9]{1,3})\s*cm', cl)
    if m: return int(m.group(1))
    # generic "<number>cm" alongside moisture
    m = re.search(r'([0-9]{1,3})\s*cm', cl)
    if m and "moisture" in cl: return int(m.group(1))
    return None

def map_soil_columns(df: pd.DataFrame) -> Dict[int, str]:
    mapping: Dict[int, str] = {}
    for c in df.columns:
        d = parse_depth_from_header(c)
        if d in TARGET_DEPTHS:
            mapping.setdefault(d, c)
        m2 = re.match(r'^soil[_\s]*moisture[_\s]*([0-9]{1,3})$', c.strip(), flags=re.I)
        if m2:
            d2 = int(m2.group(1))
            if d2 in TARGET_DEPTHS:
                mapping.setdefault(d2, c)
    return mapping

def coerce_float(val) -> Optional[float]:
    if pd.isna(val):
        return None
    try:
        return float(val)
    except Exception:
        return None

# --- API Calls ---
# POST /api/v1/dataset/ with the payload to upload sensor data.
def post_dataset(base_url: str, token: str, payload: List[Dict[str, Any]]) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/v1/dataset/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=120)
    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}
    if resp.status_code >= 400:
        raise RuntimeError(f"POST {url} failed ({resp.status_code}): {data}")
    return data

# --- API Calls ---
# GET /api/v1/dataset/{dataset_id}/analysis to fetch analysis results (e.g. irrigation events, saturation days).
def get_analysis(base_url: str, token: str, dataset_id: str) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/v1/dataset/{dataset_id}/analysis"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    params  = {
        "formatting": "JSON"
    }
    resp = requests.get(url, headers=headers, params=params, timeout=60)
    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}
    if resp.status_code >= 400:
        raise RuntimeError(f"GET {url} failed ({resp.status_code}): {data}")
    return data

def extract_event_dates(analysis: Dict[str, Any], candidates: List[str]) -> List[pd.Timestamp]:
    found = None
    for k in analysis.keys():
        for c in candidates:
            if k.lower() == c.lower():
                found = analysis[k]; break
        if found is not None: break
    if found is None:
        for k in analysis.keys():
            for c in candidates:
                if c.lower() in k.lower():
                    found = analysis[k]; break
            if found is not None: break
    if not found:
        return []
    if isinstance(found, dict) and "dates" in found:
        found = found["dates"]
    if not isinstance(found, (list, tuple)):
        found = [found]
    out: List[pd.Timestamp] = []
    for v in found:
        try:
            out.append(pd.to_datetime(v, utc=True))
        except Exception:
            pass
    if not out:
        return []
    out = sorted(pd.Series(out).drop_duplicates().tolist())
    return out

def ensure_missing_soil_depths(df: pd.DataFrame, depth_to_col: Dict[int, str], date_col: str) -> pd.DataFrame:
    # add zero columns for missing depths
    for d in TARGET_DEPTHS:
        if d not in depth_to_col:
            new_col = f"soil_moisture_{d}"
            df[new_col] = 0.0
            depth_to_col[d] = new_col
    # normalize and sort by date
    df[date_col] = pd.to_datetime(df[date_col], utc=True, errors="coerce")
    return df.sort_values(by=date_col).reset_index(drop=True)

# --- Payload Builder ---
# Convert each CSV row into a dictionary matching the API schema.
# Ensure every row has dataset_id, date, rain, temperature, humidity, and all soil_moisture_X values.
# Collect all rows into a list payload.
def build_payload(
    df: pd.DataFrame, dataset_id: str, date_col: str,
    depth_to_col: Dict[int, str], rain_col: str, temp_col: str, hum_col: str
) -> List[Dict[str, Any]]:
    payload: List[Dict[str, Any]] = []
    zeros_cols = {col for col in df.columns if df[col].dtype != object and df[col].eq(0.0).all()}
    for _, row in df.iterrows():
        item = {
            "dataset_id": dataset_id,
            "date": isoformat_utc(row[date_col]),
            "rain": float(row[rain_col]) if not pd.isna(row[rain_col]) else 0.0,
            "temperature": float(row[temp_col]) if not pd.isna(row[temp_col]) else 0.0,
            "humidity": float(row[hum_col]) if not pd.isna(row[hum_col]) else 0.0,
        }
        for d in TARGET_DEPTHS:
            key = f"soil_moisture_{d}"
            col = depth_to_col.get(d)
            if col in zeros_cols:
                item[key] = 0.0
            else:
                item[key] = coerce_float(row[col]) if col in df.columns else 0.0
        payload.append(item)
    return payload

# --- Plotting (optional) ---
# If --plot flag is provided:
#   - Plot soil moisture curves for each depth vs. date.
#   - Add vertical lines for irrigation (red) and saturation (blue).
#   - Save PNG figures.
def plot_soil_with_markers(
    df: pd.DataFrame, date_col: str, depth_to_col: Dict[int, str],
    events: List[pd.Timestamp], color: str, title: str, outfile: str
):
    plt.figure(figsize=(12, 6))
    for d in TARGET_DEPTHS:
        col = depth_to_col[d]
        if col in df.columns:
            plt.plot(df[date_col], df[col], label=col)
    for t in events:
        plt.axvline(t, color=color, linestyle='--', alpha=0.7)
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Soil moisture")
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig(outfile, dpi=150)
    print(f"[saved] {outfile}")
    plt.close()

# ======================
# Main
# ======================
def main():
    ap = argparse.ArgumentParser(description="CSV -> POST /dataset -> GET /analysis -> plots (no dateutil)")
    ap.add_argument("--csv", required=True, help="Path to CSV file")
    ap.add_argument("--base-url", required=True, help="Service base URL (e.g., https://irm.test.horizon-openagri.eu)")
    ap.add_argument("--token", required=True, help="Bearer token")
    ap.add_argument("--dataset-id", required=True, help="Dataset ID to send & query analysis for")
    ap.add_argument("--plot", action="store_true", help="Generate and save soil moisture plots")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)

    date_col = find_date_column(df)
    rain_col = detect_rain_col(df)
    temp_col = detect_temp_col(df)
    hum_col = detect_humidity_col(df)

    depth_to_col = map_soil_columns(df)
    df = ensure_missing_soil_depths(df, depth_to_col, date_col)

    payload = build_payload(
        df=df, dataset_id=args.dataset_id, date_col=date_col,
        depth_to_col=depth_to_col, rain_col=rain_col, temp_col=temp_col, hum_col=hum_col
    )
    print(f"Prepared payload with {len(payload)} rows")

    print("Posting dataset...")
    post_resp = post_dataset(args.base_url, args.token, payload)
    print("POST response (truncated):", json.dumps(post_resp, indent=2)[:1000], "...\n")

    print("Fetching analysis...")
    analysis = get_analysis(args.base_url, args.token, args.dataset_id)
    print("Analysis (truncated):", json.dumps(analysis, indent=2)[:1200], "...\n")

    irrigation_events = extract_event_dates(
        analysis, ["high_dose_irrigation_events_dates"]
    )
    saturation_days = extract_event_dates(
        analysis, ["saturation_dates"]
    )

    if args.plot:
        plot_soil_with_markers(
            df, date_col, depth_to_col, irrigation_events,
            color="red",
            title="Soil moisture vs Date (High-dose Irrigation Events)",
            outfile="soil_moisture_irrigation_events.png",
        )
        plot_soil_with_markers(
            df, date_col, depth_to_col, saturation_days,
            color="blue",
            title="Soil moisture vs Date (Saturation Days)",
            outfile="soil_moisture_saturation_days.png",
        )
        print("Saved.")
    else:
        print("Skipping plots (use --plot to enable).")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
