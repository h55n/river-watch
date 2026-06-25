"""
ndwi_baseline.py — Signal 2 (part 1): Sentinel-2 NDWI water/sediment masking.

Computes the Normalized Difference Water Index (NDWI = (Green - NIR) / (Green + NIR))
for a segment AOI, used to separate water from exposed sandbar/sediment. This is the
raw per-pass mask; segment-wise time series + seasonal baseline comparison lives in
seasonal_baseline_builder.py.

Honest framing: NDWI tells you where water vs. exposed land is *at the surface*,
on a given cloud-free-ish pass. It says nothing about depth, volume removed, or
what's under the water. Sentinel-1 is used as a cloud-cover backup precisely
because optical is blind under cloud -- see sar_anomaly.py for that path.
"""

from __future__ import annotations

from typing import Optional

import ee

from pipeline.gee_auth import init_ee

S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"

# Sentinel-2 cloud probability collection, used to mask cloudy pixels before NDWI.
S2_CLOUD_PROB_COLLECTION = "COPERNICUS/S2_CLOUD_PROBABILITY"

DEFAULT_CLOUD_PROB_THRESHOLD = 40  # %, pixels above this are masked out
DEFAULT_NDWI_WATER_THRESHOLD = 0.0  # NDWI > 0 is conventionally "water-like"


def _mask_clouds(image: "ee.Image", cloud_prob: "ee.Image", threshold: int) -> "ee.Image":
    cloud_mask = cloud_prob.select("probability").lt(threshold)
    return image.updateMask(cloud_mask)


def get_ndwi_image(
    aoi: "ee.Geometry",
    start: str,
    end: str,
    cloud_prob_threshold: int = DEFAULT_CLOUD_PROB_THRESHOLD,
) -> Optional["ee.Image"]:
    """
    Return a cloud-masked, median-composited NDWI image for the AOI/date range.
    Returns None (well, an ee.Image that will evaluate empty) if no scenes exist
    in range -- callers should check collection size before assuming success on
    a synchronous round-trip.
    """
    init_ee()

    s2 = ee.ImageCollection(S2_COLLECTION).filterBounds(aoi).filterDate(start, end)
    cloud_prob = (
        ee.ImageCollection(S2_CLOUD_PROB_COLLECTION).filterBounds(aoi).filterDate(start, end)
    )

    joined = ee.Join.saveFirst("cloud_prob").apply(
        primary=s2,
        secondary=cloud_prob,
        condition=ee.Filter.equals(leftField="system:index", rightField="system:index"),
    )

    def _add_masked_ndwi(img):
        img = ee.Image(img)
        cp = ee.Image(img.get("cloud_prob"))
        masked = _mask_clouds(img, cp, cloud_prob_threshold)
        ndwi = masked.normalizedDifference(["B3", "B8"]).rename("NDWI")
        return ndwi

    ndwi_coll = ee.ImageCollection(joined).map(_add_masked_ndwi)
    return ndwi_coll.median().clip(aoi)


def get_water_mask(
    ndwi_image: "ee.Image", threshold: float = DEFAULT_NDWI_WATER_THRESHOLD
) -> "ee.Image":
    """Binary water mask (1 = water-like, 0 = exposed sediment/sandbar/land)."""
    return ndwi_image.gt(threshold).rename("water_mask")


def get_sandbar_area_sq_m(
    aoi: "ee.Geometry", ndwi_image: "ee.Image", scale: int = 10
) -> float:
    """
    Compute exposed (non-water) area within the AOI for one pass. This is the
    raw scalar that seasonal_baseline_builder.py aggregates into a time series.
    """
    init_ee()
    water_mask = get_water_mask(ndwi_image)
    sandbar_mask = water_mask.Not().rename("sandbar")
    pixel_area = ee.Image.pixelArea()

    stats = sandbar_mask.multiply(pixel_area).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=aoi, scale=scale, maxPixels=1e10
    )
    info = stats.getInfo()
    return float(info.get("sandbar") or 0.0)
