"""
sar_anomaly.py — Signal 1: Equipment & Vessel Presence via Sentinel-1 backscatter anomaly.

Honest framing (do not violate, see spec Section 2.1):
  - This does NOT measure riverbed depth or elevation. SAR does not see through
    river water to the bed.
  - This DOES detect strong, localized specular radar returns consistent with
    metal equipment (dredgers, excavators, trucks) sitting on or near an
    otherwise "quiet" sandbar/riverbed zone -- the same physics used for
    ship detection at sea.

Method:
  1. Pull Sentinel-1 GRD (C-band), VV and VH polarization, over the segment AOI.
  2. For each pass, compute a log-ratio against a smoothed reference image
     built from a trailing window of "normal" passes (the seasonal baseline,
     see seasonal_baseline_builder.py).
  3. Flag pixels/clusters whose log-ratio exceeds a noise-adjusted threshold.
  4. Return a per-pass anomaly raster + a scalar score (flagged pixel count,
     area, and peak intensity) for combination in anomaly_scorer.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import ee

from pipeline.gee_auth import init_ee

S1_COLLECTION = "COPERNICUS/S1_GRD"

# Noise-adjusted threshold (dB) for log-ratio flagging. Sentinel-1 GRD speckle
# noise floor is roughly ~0.5-1 dB after multilooking; 3 dB gives a healthy
# margin against false positives from speckle alone. Tune per-segment once you
# have real backtest data -- this is a starting default, not a calibrated constant.
DEFAULT_THRESHOLD_DB = 3.0


@dataclass
class SarAnomalyResult:
    segment_id: str
    pass_date: str
    threshold_db: float
    flagged_pixel_count: Optional[int] = None
    flagged_area_sq_m: Optional[float] = None
    peak_log_ratio_db: Optional[float] = None
    image: "ee.Image | None" = None  # the anomaly raster, for map display / export


def _s1_collection(aoi: "ee.Geometry", start: str, end: str) -> "ee.ImageCollection":
    """Filtered Sentinel-1 GRD collection: IW mode, VV+VH, over the AOI/date range."""
    return (
        ee.ImageCollection(S1_COLLECTION)
        .filterBounds(aoi)
        .filterDate(start, end)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .select(["VV", "VH"])
    )


def build_reference_image(
    aoi: "ee.Geometry", reference_start: str, reference_end: str
) -> "ee.Image":
    """
    Build a smoothed reference ("quiet baseline") image by median-compositing
    Sentinel-1 passes over a trailing window assumed to be free of known
    incidents. This is distinct from the *seasonal* baseline in
    seasonal_baseline_builder.py, which tracks Signal 2 (morphology) over a
    full year; this reference is a shorter-window radar quiet-state for
    log-ratio comparison.
    """
    init_ee()
    coll = _s1_collection(aoi, reference_start, reference_end)
    return coll.median().clip(aoi)


def detect_anomaly(
    segment_id: str,
    aoi: "ee.Geometry",
    pass_date: str,
    reference_image: "ee.Image",
    threshold_db: float = DEFAULT_THRESHOLD_DB,
    window_days: int = 1,
) -> SarAnomalyResult:
    """
    Compute the log-ratio anomaly raster for the Sentinel-1 pass nearest
    `pass_date` against `reference_image`, and flag pixels exceeding threshold.

    Returns a SarAnomalyResult with the anomaly image attached. Scalar stats
    (flagged_pixel_count etc.) require a .getInfo() reduction call, which is
    deliberately NOT done here so callers can batch/export instead of forcing
    a synchronous round-trip for every segment. Call `.reduce_stats()` helper
    below (or do it inline) when you actually need the numbers.
    """
    init_ee()

    target_dt = datetime.strptime(pass_date, "%Y-%m-%d")
    start = (target_dt - timedelta(days=window_days)).strftime("%Y-%m-%d")
    end = (target_dt + timedelta(days=window_days + 1)).strftime("%Y-%m-%d")

    coll = _s1_collection(aoi, start, end)
    pass_image = coll.median().clip(aoi)  # median across the small window if >1 pass

    # log-ratio in dB: 10 * log10(pass / reference), per band
    log_ratio = pass_image.divide(reference_image).log10().multiply(10).rename(
        ["VV_logratio", "VH_logratio"]
    )

    flagged_mask = log_ratio.select("VV_logratio").gt(threshold_db).Or(
        log_ratio.select("VH_logratio").gt(threshold_db)
    )

    anomaly_image = log_ratio.addBands(flagged_mask.rename("flagged"))

    return SarAnomalyResult(
        segment_id=segment_id,
        pass_date=pass_date,
        threshold_db=threshold_db,
        image=anomaly_image,
    )


def reduce_stats(
    result: SarAnomalyResult, aoi: "ee.Geometry", scale: int = 10
) -> SarAnomalyResult:
    """
    Run the actual getInfo() reduction to populate scalar stats on a
    SarAnomalyResult. Separated from detect_anomaly() so batch pipelines can
    decide when to pay the network round-trip cost.
    """
    if result.image is None:
        return result

    flagged = result.image.select("flagged")
    pixel_area = ee.Image.pixelArea()

    area_stats = flagged.multiply(pixel_area).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=aoi, scale=scale, maxPixels=1e10
    )
    count_stats = flagged.reduceRegion(
        reducer=ee.Reducer.sum(), geometry=aoi, scale=scale, maxPixels=1e10
    )
    peak_stats = result.image.select(["VV_logratio", "VH_logratio"]).reduceRegion(
        reducer=ee.Reducer.max(), geometry=aoi, scale=scale, maxPixels=1e10
    )

    info_area = area_stats.getInfo()
    info_count = count_stats.getInfo()
    info_peak = peak_stats.getInfo()

    result.flagged_area_sq_m = info_area.get("flagged")
    result.flagged_pixel_count = info_count.get("flagged")
    result.peak_log_ratio_db = max(
        (v for v in info_peak.values() if v is not None), default=None
    )
    return result
