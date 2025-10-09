#!/usr/bin/env python3
"""
eto_pipeline.py

Creates a parcel (WKT) in the Irrigation service, picks the first location,
retrieves ETo calculations for a date range, and plots the results.

Endpoints used:
  POST /api/v1/location/parcel-wkt/
  GET  /api/v1/location/
  GET  /api/v1/eto/get-calculations/{location_id}/from/{from_date}/to/{to_date}/

Requirements:
  pip install requests matplotlib
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ---- Helpers ----------------------------------------------------------------

def headers(token: str) -> Dict[str, str]:
    """Build common headers for authenticated JSON requests."""
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

def pretty(obj: Any, limit: int = 1000) -> str:
    """Human-friendly JSON printer with length cap."""
    try:
        s = json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        s = str(obj)
    return (s[:limit] + " ...") if len(s) > limit else s

def parse_iso_date(d: str) -> datetime:
    """Parse 'YYYY-MM-DD' (or ISO-like) into datetime (naive)."""
    try:
        if len(d) >= 19 and d[4] == "-" and d[7] == "-" and d[10] == "T":
            return datetime.fromisoformat(d.replace("Z", "+00:00")).replace(tzinfo=None)
        return datetime.strptime(d[:10], "%Y-%m-%d")
    except Exception:
        return datetime.strptime(d[:10], "%Y-%m-%d")

# ---- API wrappers ------------------------------------------------------------

def create_parcel(base_url: str, token: str, wkt: str) -> Dict[str, Any]:
    """
    Create parcel by WKT.
    POST /api/v1/location/parcel-wkt/
    Body: {"coordinates": "<WKT POLYGON>"}
    """
    url = f"{base_url.rstrip('/')}/api/v1/location/parcel-wkt/"
    body = {"coordinates": wkt}
    resp = requests.post(url, headers=headers(token), data=json.dumps(body), timeout=60)
    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}
    if resp.status_code >= 400:
        raise RuntimeError(f"Create parcel failed ({resp.status_code}): {pretty(data)}")
    return data

def list_locations(base_url: str, token: str) -> List[Dict[str, Any]]:
    """
    List all locations.
    GET /api/v1/location/
    """
    url = f"{base_url.rstrip('/')}/api/v1/location/"
    resp = requests.get(url, headers=headers(token), timeout=60)
    try:
        data = resp.json()
    except Exception:
        data = []
    if resp.status_code >= 400:
        raise RuntimeError(f"List locations failed ({resp.status_code}): {pretty(data)}")
    if isinstance(data, list):
        return data
    # tolerate wrappers like {"results":[...]} or {"data":[...]}
    for key in ("results", "data", "locations"):
        if key in data and isinstance(data[key], list):
            return data[key]
    return []

def get_eto_calculations(base_url: str, token: str, location_id: str, from_date: str, to_date: str) -> Dict[str, Any]:
    """
    Fetch ETo time series for a location in a given date range.
    GET /api/v1/eto/get-calculations/{location_id}/from/{from_date}/to/{to_date}/
    """
    path = f"/api/v1/eto/get-calculations/{location_id}/from/{from_date}/to/{to_date}/"
    url = f"{base_url.rstrip('/')}{path}"
    resp = requests.get(url, headers=headers(token), timeout=60)
    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}
    if resp.status_code >= 400:
        raise RuntimeError(f"ETo calculations failed ({resp.status_code}): {pretty(data)}")
    return data

# ---- Parsing & plotting ------------------------------------------------------

def extract_eto_series(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Given {"calculations":[{"date":"YYYY-MM-DD","value":float}, ...]},
    return sorted series: [{"date": datetime, "value": float}, ...]
    """
    calcs = payload.get("calculations", [])
    series: List[Dict[str, Any]] = []
    for item in calcs:
        if not isinstance(item, dict):
            continue
        d = item.get("date")
        v = item.get("value")
        if d is None or v is None:
            continue
        try:
            series.append({"date": parse_iso_date(str(d)), "value": float(v)})
        except Exception:
            continue
    series.sort(key=lambda x: x["date"])
    return series

def plot_eto(series: List[Dict[str, Any]], outfile: str = "eto_plot.png") -> None:
    """
    Plot ETo vs date:
      - x-axis labeled as MM-DD (no year)
      - show ALL dates as ticks
      - annotate each point as (MM-DD, value)
    """
    if not series:
        print("No ETo data to plot.")
        return

    dates = [p["date"] for p in series]
    vals  = [p["value"] for p in series]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, vals, label="ETo (mm/day)")
    ax.scatter(dates, vals, s=25)

    # Format x-axis as MM-DD, show all ticks
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax.set_xticks(dates)
    plt.xticks(rotation=45, ha='right', fontsize=8)

    # Annotate each point as (MM-DD, value)
    for d, y in zip(dates, vals):
        ax.annotate(
            f"({d:%m-%d}, {y:.2f})",
            xy=(d, y),
            xytext=(4, 6),
            textcoords="offset points",
            fontsize=8,
            rotation=30,
        )

    ax.set_title("Reference Evapotranspiration (ETo)")
    ax.set_xlabel("Date (MM-DD)")
    ax.set_ylabel("ETo (mm/day)")
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    print(f"[saved] {outfile}")
    plt.close(fig)

# ---- Main -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Create parcel (WKT), pick first location, fetch and plot ETo calculations.")
    parser.add_argument("--base-url", required=True, help="Service base URL (e.g., https://irm.test.horizon-openagri.eu)")
    parser.add_argument("--token", required=True, help="JWT Bearer token")
    parser.add_argument("--wkt", required=True, help="WKT POLYGON string used to create a parcel")
    parser.add_argument("--from-date", required=True, help="From date (YYYY-MM-DD)")
    parser.add_argument("--to-date", required=True, help="To date (YYYY-MM-DD)")
    parser.add_argument("--plot", action="store_true", help="Skip plotting if set")
    args = parser.parse_args()

    # 1) Create a parcel from WKT POLYGON
    print("Creating parcel (WKT)...")
    parcel_resp = create_parcel(args.base_url, args.token, args.wkt)
    print("Parcel response:", pretty(parcel_resp))

    # 2) List all locations and choose the first one
    print("\nListing locations...")
    locations = list_locations(args.base_url, args.token)
    if not locations:
        raise RuntimeError("No locations returned by /api/v1/location/. Ensure parcel creation succeeded.")
    first = locations[0]
    location_id = str(first.get("id") or first.get("uuid") or first.get("location_id") or "")
    if not location_id:
        raise RuntimeError(f"Could not determine location id from first entry: {pretty(first)}")
    print(f"Using location id (first): {location_id}")

    # 3) Get ETo calculations for date range
    print("\nFetching ETo calculations...")
    eto_json = get_eto_calculations(args.base_url, args.token, location_id, args.from_date, args.to_date)
    print("ETo response (truncated):", pretty(eto_json))

    # 4) Parse and (optionally) plot
    series = extract_eto_series(eto_json)
    print(f"Parsed {len(series)} ETo points.")
    if args.plot:
        plot_eto(series, outfile="eto_plot.png")
    else:
        print("Plotting skipped (--no-plot).")

    print("\nDone.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
