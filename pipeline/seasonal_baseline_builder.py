"""
seasonal_baseline_builder.py — rolling, segment-specific seasonal baseline for
Signal 2 (sandbar/bankline morphology).

This is the single most important anti-false-positive component in the whole
pipeline (see spec Section 2.2 and Section 9): a raw before/after sandbar-area
comparison will misfire constantly on ordinary monsoon-driven channel shifts.
Every segment gets its OWN baseline, built from its OWN history -- never a
global threshold shared across segments.

Approach:
  1. Pull historical Sentinel-2 NDWI passes for the segment, going back N years.
  2. For each pass, compute exposed sandbar area (ndwi_baseline.get_sandbar_area_sq_m).
  3. Bucket by day-of-year (or month) to build an expected range (e.g. 10th-90th
     percentile) for "what's normal at this time of year, on this segment".
  4. Cache the result to data/baselines/baseline_<segment_id>.json so repeat runs
     don't re-hit Earth Engine for historical data that doesn't change.
  5. anomaly_scorer.py compares a new pass's sandbar area against this baseline
     range for the matching time-of-year bucket.
"""

from __future__ import annotations

import json
import os
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import ee

from pipeline.gee_auth import init_ee
from pipeline.ndwi_baseline import get_ndwi_image, get_sandbar_area_sq_m

BASELINE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "baselines")


@dataclass
class MonthlyBaseline:
    month: int  # 1-12
    n_samples: int
    p10_sq_m: float
    median_sq_m: float
    p90_sq_m: float


@dataclass
class SegmentBaseline:
    segment_id: str
    built_at: str
    history_years: int
    monthly: List[MonthlyBaseline]

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    def get_month(self, month: int) -> Optional[MonthlyBaseline]:
        for m in self.monthly:
            if m.month == month:
                return m
        return None


def _baseline_path(segment_id: str) -> str:
    return os.path.join(BASELINE_DIR, f"baseline_{segment_id}.json")


def _sample_dates(years_back: int, samples_per_month: int = 2) -> List[str]:
    """
    Generate a list of representative sample dates going back `years_back` years,
    `samples_per_month` per month, used to query historical Sentinel-2 passes.
    Sentinel-2 coverage realistically starts 2015-2017 depending on region --
    don't reach further back than actual archive availability.
    """
    today = datetime.now(timezone.utc)
    dates = []
    for y in range(1, years_back + 1):
        year = today.year - y
        for month in range(1, 13):
            for i in range(samples_per_month):
                day = 5 + i * 15  # spread within the month, avoids month-end overflow
                dates.append(f"{year:04d}-{month:02d}-{day:02d}")
    return dates


def build_segment_baseline(
    segment_id: str,
    aoi: "ee.Geometry",
    years_back: int = 5,
    window_days: int = 10,
    save: bool = True,
) -> SegmentBaseline:
    """
    Build (or rebuild) the seasonal baseline for a segment by sampling historical
    NDWI-derived sandbar area across `years_back` years, bucketed by month.

    This makes one Earth Engine round-trip per sample date -- for years_back=5
    and 2 samples/month that's 120 calls, which is fine for a one-time/occasional
    build but should NOT be re-run on every page load. Cache via `save=True` and
    have the app read the cached JSON (see app/components/baseline_chart.py).
    """
    init_ee()

    monthly_samples: Dict[int, List[float]] = {m: [] for m in range(1, 13)}

    for date_str in _sample_dates(years_back):
        target = datetime.strptime(date_str, "%Y-%m-%d")
        start = (target - timedelta(days=window_days)).strftime("%Y-%m-%d")
        end = (target + timedelta(days=window_days)).strftime("%Y-%m-%d")
        try:
            ndwi_img = get_ndwi_image(aoi, start, end)
            area = get_sandbar_area_sq_m(aoi, ndwi_img)
            if area and area > 0:
                monthly_samples[target.month].append(area)
        except Exception:
            # Missing/cloudy scenes for a given window are expected and should not
            # halt the whole baseline build -- just skip that sample.
            continue

    monthly: List[MonthlyBaseline] = []
    for month, samples in monthly_samples.items():
        if len(samples) < 2:
            continue
        samples_sorted = sorted(samples)
        monthly.append(
            MonthlyBaseline(
                month=month,
                n_samples=len(samples),
                p10_sq_m=_percentile(samples_sorted, 10),
                median_sq_m=statistics.median(samples_sorted),
                p90_sq_m=_percentile(samples_sorted, 90),
            )
        )

    baseline = SegmentBaseline(
        segment_id=segment_id,
        built_at=datetime.now(timezone.utc).isoformat(),
        history_years=years_back,
        monthly=monthly,
    )

    if save:
        save_baseline(baseline)

    return baseline


def _percentile(sorted_values: List[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * (pct / 100)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


def save_baseline(baseline: SegmentBaseline) -> str:
    os.makedirs(BASELINE_DIR, exist_ok=True)
    path = _baseline_path(baseline.segment_id)
    with open(path, "w") as f:
        json.dump(baseline.to_dict(), f, indent=2)
    return path


def load_baseline(segment_id: str) -> Optional[SegmentBaseline]:
    path = _baseline_path(segment_id)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        raw = json.load(f)
    monthly = [MonthlyBaseline(**m) for m in raw["monthly"]]
    return SegmentBaseline(
        segment_id=raw["segment_id"],
        built_at=raw["built_at"],
        history_years=raw["history_years"],
        monthly=monthly,
    )


def is_within_seasonal_range(
    baseline: SegmentBaseline, month: int, observed_sq_m: float, margin: float = 0.0
) -> Optional[bool]:
    """
    Returns True if observed_sq_m falls within [p10, p90] (+/- margin) for that
    month's baseline. Returns None if there's no baseline data for that month
    yet (e.g. brand-new segment, baseline not built) -- callers MUST treat None
    as "cannot assess seasonality" and avoid flagging an anomaly purely on
    morphology in that case, per spec Section 2.2's gotcha-question concern.
    """
    bucket = baseline.get_month(month)
    if bucket is None:
        return None
    lower = bucket.p10_sq_m * (1 - margin)
    upper = bucket.p90_sq_m * (1 + margin)
    return lower <= observed_sq_m <= upper
