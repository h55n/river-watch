"""
gfw_client.py — Global Forest Watch (WRI) public API client.

Used per spec Section 2.1/2.2: River Watch does NOT build its own deforestation
detector. GFW + RADD alerts already solve that at planetary scale using
Sentinel-1 SAR, updated weekly. This client fetches their public data as a
CREDITED REFERENCE LAYER ONLY -- it should always be labeled in the UI as
"Source: Global Forest Watch / RADD alerts (WRI)", never presented as River
Watch's own detection work.

GFW's Data API is documented at https://data-api.globalforestwatch.org/
This client uses the public, no-key-required endpoints where available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import requests

GFW_DATA_API_BASE = "https://data-api.globalforestwatch.org"
GFW_ATTRIBUTION = "Source: Global Forest Watch / RADD alerts (World Resources Institute)"


class GfwClientError(RuntimeError):
    pass


@dataclass
class ForestAlert:
    latitude: float
    longitude: float
    alert_date: str
    confidence: Optional[str]
    source: str = "RADD"


def fetch_radd_alerts_for_bbox(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    start_date: str,
    end_date: str,
    dataset: str = "gfw_radd_alerts",
) -> List[ForestAlert]:
    """
    Fetch RADD deforestation alerts intersecting a bounding box and date range.

    This is a thin wrapper around GFW's Data API query endpoint. The exact
    dataset slug/version can change -- check https://data-api.globalforestwatch.org/
    docs before relying on this in production, and treat dataset="gfw_radd_alerts"
    as a placeholder to verify, not a guaranteed-stable identifier.

    Returns an empty list (not an error) if no alerts fall in range -- that's
    the expected common case for most river segments most weeks.
    """
    query = {
        "sql": (
            "SELECT latitude, longitude, alert_date, confidence "
            f"FROM {dataset} "
            f"WHERE alert_date >= '{start_date}' AND alert_date <= '{end_date}' "
            f"AND latitude BETWEEN {min_lat} AND {max_lat} "
            f"AND longitude BETWEEN {min_lon} AND {max_lon}"
        )
    }

    try:
        resp = requests.get(f"{GFW_DATA_API_BASE}/dataset/{dataset}/latest/query", params=query, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise GfwClientError(
            f"GFW request failed (verify dataset slug/endpoint against current "
            f"GFW Data API docs): {exc}"
        ) from exc

    data = resp.json().get("data", [])
    alerts: List[ForestAlert] = []
    for row in data:
        try:
            alerts.append(
                ForestAlert(
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    alert_date=row["alert_date"],
                    confidence=row.get("confidence"),
                )
            )
        except (KeyError, ValueError):
            continue

    return alerts
