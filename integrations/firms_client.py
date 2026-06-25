"""
firms_client.py — NASA FIRMS (Fire Information for Resource Management System) client.

Used per spec Section 2.2, Signal 3: a genuinely near-real-time supplementary
overlay (fire/thermal anomalies -- e.g. kiln burning, land-clearing fires near
mining sites) that makes the map feel alive WITHOUT overstating SAR/optical's
own multi-day revisit cadence. This is reference data only -- never presented
as River Watch's own detection.

FIRMS provides a free API; an API key (also free) is required for the
area/CSV endpoints used here. Register at https://firms.modaps.eosdis.nasa.gov/api/
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional

import requests

FIRMS_BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

# VIIRS_SNPP_NRT is a good default: ~375m resolution, near-real-time (often
# within a few hours), good fit for India coverage. Swap to MODIS_NRT for
# longer historical archive at coarser (1km) resolution if needed.
DEFAULT_SOURCE = "VIIRS_SNPP_NRT"


@dataclass
class FirePoint:
    latitude: float
    longitude: float
    acq_date: str
    acq_time: str
    confidence: str
    frp: Optional[float]  # Fire Radiative Power, MW -- rough intensity proxy


class FirmsClientError(RuntimeError):
    pass


def _get_api_key() -> str:
    key = os.environ.get("FIRMS_API_KEY")
    if not key:
        raise FirmsClientError(
            "FIRMS_API_KEY not set. Get a free key at "
            "https://firms.modaps.eosdis.nasa.gov/api/ and set it as an env var."
        )
    return key


def fetch_fire_points(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    days_back: int = 1,
    source: str = DEFAULT_SOURCE,
) -> List[FirePoint]:
    """
    Fetch recent thermal anomaly points within a bounding box.

    Args:
        min_lon, min_lat, max_lon, max_lat: bounding box (degrees)
        days_back: 1-10, how many days of data to pull
        source: FIRMS sensor source, see FIRMS API docs for the full list

    Returns: list of FirePoint. Empty list if no detections (this is the
    common/expected case for most queries, not an error).
    """
    api_key = _get_api_key()
    bbox = f"{min_lon},{min_lat},{max_lon},{max_lat}"
    url = f"{FIRMS_BASE_URL}/{api_key}/{source}/{bbox}/{days_back}"

    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise FirmsClientError(f"FIRMS request failed: {exc}") from exc

    lines = resp.text.strip().splitlines()
    if not lines or len(lines) < 2:
        return []  # header only / empty response = no detections, not an error

    header = lines[0].split(",")
    points: List[FirePoint] = []
    for line in lines[1:]:
        values = line.split(",")
        row = dict(zip(header, values))
        try:
            points.append(
                FirePoint(
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    acq_date=row.get("acq_date", ""),
                    acq_time=row.get("acq_time", ""),
                    confidence=row.get("confidence", ""),
                    frp=float(row["frp"]) if row.get("frp") else None,
                )
            )
        except (KeyError, ValueError):
            continue  # skip malformed rows rather than failing the whole fetch

    return points
