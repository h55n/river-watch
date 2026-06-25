"""
imagery_fetcher.py
Generates GEE thumbnail URLs for actual Sentinel-1 and Sentinel-2 imagery.
These URLs render server-side on GEE and can be loaded directly in st.image()
or displayed in <img> tags. No image download required.

Honest framing:
- URLs returned are static PNG thumbnails, not live tile feeds.
- GEE getThumbURL() has rate limits — do NOT call from Streamlit page-load.
  Cache results via cache_imagery_for_segment() and load from JSON at runtime.
- All imagery: Copernicus Sentinel data (ESA), open licence.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

import ee


def get_s2_truecolor_thumbnail(
    bbox: list,            # [lon_min, lat_min, lon_max, lat_max]
    start_date: str,       # 'YYYY-MM-DD'
    end_date: str,
    dimensions: int = 512,
    max_cloud_pct: float = 20.0,
) -> tuple[Optional[str], Optional[str]]:
    """
    Returns (url, date_str) for the least-cloudy Sentinel-2 true-colour
    composite in the given date window. Returns (None, None) if no imagery found.

    DISPLAY LABEL: 'Sentinel-2 True Colour (RGB: B4/B3/B2)'
    NEVER label this as a live or real-time image. Always show the actual
    acquisition date returned as date_str.
    """
    try:
        region = ee.Geometry.BBox(bbox[0], bbox[1], bbox[2], bbox[3])

        collection = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(region)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud_pct))
            .sort("CLOUDY_PIXEL_PERCENTAGE")
        )

        count = collection.size().getInfo()
        if count == 0:
            return None, None

        image = collection.first()
        date_str = image.date().format("YYYY-MM-dd").getInfo()

        url = image.getThumbURL({
            "bands": ["B4", "B3", "B2"],
            "min": 200,
            "max": 3000,
            "gamma": 1.4,
            "region": region,
            "dimensions": dimensions,
            "format": "png",
        })

        return url, date_str
    except Exception as e:
        print(f"[imagery_fetcher] S2 true-colour fetch failed: {e}")
        return None, None


def get_s2_ndwi_thumbnail(
    bbox: list,
    start_date: str,
    end_date: str,
    dimensions: int = 512,
    max_cloud_pct: float = 20.0,
) -> tuple[Optional[str], Optional[str]]:
    """
    Returns (url, date_str) for a NDWI composite.
    NDWI = (B3 - B8) / (B3 + B8)
    Colour key: Brown/wheat = dry/exposed sandbar, Blue = water channel.

    DISPLAY LABEL: 'Sentinel-2 NDWI (Water/Sandbar Index)'
    """
    try:
        region = ee.Geometry.BBox(bbox[0], bbox[1], bbox[2], bbox[3])

        collection = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(region)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud_pct))
            .sort("CLOUDY_PIXEL_PERCENTAGE")
        )

        if collection.size().getInfo() == 0:
            return None, None

        image = collection.first()
        date_str = image.date().format("YYYY-MM-dd").getInfo()
        ndwi = image.normalizedDifference(["B3", "B8"]).rename("NDWI")

        url = ndwi.getThumbURL({
            "min": -0.3,
            "max": 0.5,
            # brown=dry sand, wheat=exposed sand, light yellow=moist sand,
            # sky blue=shallow water, blue=deep water
            "palette": ["#8B4513", "#F5DEB3", "#FFFACD", "#87CEEB", "#0000FF"],
            "region": region,
            "dimensions": dimensions,
            "format": "png",
        })

        return url, date_str
    except Exception as e:
        print(f"[imagery_fetcher] S2 NDWI fetch failed: {e}")
        return None, None


def get_s1_sar_thumbnail(
    bbox: list,
    start_date: str,
    end_date: str,
    dimensions: int = 512,
    polarization: str = "VV",
) -> tuple[Optional[str], Optional[str]]:
    """
    Returns (url, date_str) for a Sentinel-1 SAR (C-band, GRD) pass.
    Bright pixels = high backscatter = metal objects/equipment/water.
    Dark pixels = smooth/absorbing surfaces = dry sand, calm water.

    DISPLAY LABEL: f'Sentinel-1 SAR ({polarization}-polarization, C-band GRD)'
    IMPORTANT: Never claim this shows "trucks" or "mining equipment" directly.
    Label as "Equipment/vessel backscatter anomaly zone" only if anomaly detected.
    """
    try:
        region = ee.Geometry.BBox(bbox[0], bbox[1], bbox[2], bbox[3])

        collection = (
            ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterBounds(region)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", polarization))
            .filter(ee.Filter.eq("instrumentMode", "IW"))
        )

        if collection.size().getInfo() == 0:
            return None, None

        image = collection.sort("system:time_start", False).first()
        date_str = image.date().format("YYYY-MM-dd").getInfo()
        band = image.select(polarization)

        # Convert to dB for display
        band_db = band.log10().multiply(10).rename("SAR_dB")

        url = band_db.getThumbURL({
            "min": -25,
            "max": 5,
            # black=very dark (calm water/sand), purples=medium,
            # orange/white=bright (metal/structures/equipment)
            "palette": ["#000000", "#1a1a2e", "#16213e", "#0f3460", "#533483",
                        "#e94560", "#f5a623", "#ffffff"],
            "region": region,
            "dimensions": dimensions,
            "format": "png",
        })

        return url, date_str
    except Exception as e:
        print(f"[imagery_fetcher] S1 SAR fetch failed: {e}")
        return None, None


def get_s1_logratio_thumbnail(
    bbox: list,
    before_start: str,
    before_end: str,
    after_start: str,
    after_end: str,
    dimensions: int = 512,
) -> tuple[Optional[str], Optional[str]]:
    """
    Generates a log-ratio change detection image between two SAR time windows.
    Red/orange = areas that INCREASED in backscatter (possible equipment arrival).
    Blue = areas that DECREASED in backscatter (removal / morphology loss).

    DISPLAY LABEL: 'SAR Backscatter Change (Log-Ratio: Before vs. After)'
    HEDGE LANGUAGE: 'Areas of significant backscatter increase may indicate
    equipment or vessel presence. Requires human review to confirm.'
    """
    try:
        region = ee.Geometry.BBox(bbox[0], bbox[1], bbox[2], bbox[3])

        def get_mean_sar(start: str, end: str) -> ee.Image:
            return (
                ee.ImageCollection("COPERNICUS/S1_GRD")
                .filterBounds(region)
                .filterDate(start, end)
                .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
                .filter(ee.Filter.eq("instrumentMode", "IW"))
                .select("VV")
                .mean()
            )

        before = get_mean_sar(before_start, before_end)
        after = get_mean_sar(after_start, after_end)

        log_ratio = after.subtract(before).rename("LogRatio")

        url = log_ratio.getThumbURL({
            "min": -3,
            "max": 3,
            # blue=decrease, white=no change, red=increase (anomaly)
            "palette": ["#2166ac", "#4393c3", "#92c5de", "#f7f7f7",
                        "#fddbc7", "#f4a582", "#d6604d", "#b2182b"],
            "region": region,
            "dimensions": dimensions,
            "format": "png",
        })

        period_label = f"{after_start} to {after_end}"
        return url, period_label
    except Exception as e:
        print(f"[imagery_fetcher] S1 log-ratio fetch failed: {e}")
        return None, None


def get_timeseries_thumbnails(
    bbox: list,
    start_date: str,
    end_date: str,
    num_images: int = 8,
    image_type: str = "S2_truecolor",  # 'S2_truecolor' | 'S1_SAR' | 'S2_NDWI'
    dimensions: int = 256,
) -> list:
    """
    Returns a list of dicts [{'url': ..., 'date': ..., 'type': ...}] representing
    a time-series of satellite passes ordered chronologically.

    Used to build the satellite pass strip in the UI — showing the actual
    sequence of imagery over the monitoring period.
    """
    try:
        region = ee.Geometry.BBox(bbox[0], bbox[1], bbox[2], bbox[3])
        results = []

        if image_type in ("S2_truecolor", "S2_NDWI"):
            collection = (
                ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                .filterBounds(region)
                .filterDate(start_date, end_date)
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
                .sort("system:time_start")
            )
        else:  # S1_SAR
            collection = (
                ee.ImageCollection("COPERNICUS/S1_GRD")
                .filterBounds(region)
                .filterDate(start_date, end_date)
                .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
                .filter(ee.Filter.eq("instrumentMode", "IW"))
                .sort("system:time_start")
            )

        total = min(collection.size().getInfo(), 40)
        if total == 0:
            return []

        step = max(1, total // num_images)
        image_list = collection.toList(total)

        for i in range(0, total, step):
            if len(results) >= num_images:
                break

            img = ee.Image(image_list.get(i))
            date_str = img.date().format("YYYY-MM-dd").getInfo()

            if image_type == "S2_truecolor":
                url = img.getThumbURL({
                    "bands": ["B4", "B3", "B2"],
                    "min": 200,
                    "max": 3000,
                    "gamma": 1.4,
                    "region": region,
                    "dimensions": dimensions,
                    "format": "png",
                })
            elif image_type == "S2_NDWI":
                ndwi = img.normalizedDifference(["B3", "B8"])
                url = ndwi.getThumbURL({
                    "min": -0.3,
                    "max": 0.5,
                    "palette": ["#8B4513", "#F5DEB3", "#FFFACD", "#87CEEB", "#0000FF"],
                    "region": region,
                    "dimensions": dimensions,
                    "format": "png",
                })
            else:  # S1_SAR
                band_db = img.select("VV").log10().multiply(10)
                url = band_db.getThumbURL({
                    "min": -25,
                    "max": 5,
                    "palette": ["#000000", "#1a1a2e", "#0f3460", "#533483",
                                "#e94560", "#f5a623", "#ffffff"],
                    "region": region,
                    "dimensions": dimensions,
                    "format": "png",
                })

            results.append({"url": url, "date": date_str, "type": image_type})

        return results
    except Exception as e:
        print(f"[imagery_fetcher] Timeseries fetch failed: {e}")
        return []


def cache_imagery_for_segment(
    segment_id: str,
    segment_meta: dict,
    cache_path: str,
) -> dict:
    """
    Pre-generates and caches all imagery URLs for a segment.
    Call this during the refresh cycle (refresh_anomaly_cache.py),
    NOT on every page load. GEE getThumbURL() calls have rate limits.

    Writes: data/imagery_cache/{segment_id}_imagery.json

    segment_meta must contain: bbox, baseline_start, baseline_end,
    incident_window_start, incident_window_end.
    """
    bbox = segment_meta["bbox"]  # [lon_min, lat_min, lon_max, lat_max]
    baseline_start = segment_meta.get("baseline_start", "2022-06-01")
    baseline_end = segment_meta.get("baseline_end", "2022-12-15")
    window_start = segment_meta.get("incident_window_start", "2022-12-20")
    window_end = segment_meta.get("incident_window_end", "2023-01-20")

    cache: dict = {
        "segment_id": segment_id,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "baseline_period": {"start": baseline_start, "end": baseline_end},
        "incident_window": {"start": window_start, "end": window_end},
        "before_truecolor": {},
        "after_truecolor": {},
        "before_ndwi": {},
        "after_ndwi": {},
        "before_sar": {},
        "after_sar": {},
        "logratio": {},
        "timeseries_s2": [],
        "timeseries_s1": [],
    }

    print(f"[imagery_fetcher] Fetching before true-colour ({baseline_start} to {baseline_end})...")
    url, date = get_s2_truecolor_thumbnail(bbox, baseline_start, baseline_end)
    cache["before_truecolor"] = {"url": url, "date": date}

    print(f"[imagery_fetcher] Fetching before NDWI...")
    url, date = get_s2_ndwi_thumbnail(bbox, baseline_start, baseline_end)
    cache["before_ndwi"] = {"url": url, "date": date}

    print(f"[imagery_fetcher] Fetching before SAR...")
    url, date = get_s1_sar_thumbnail(bbox, baseline_start, baseline_end)
    cache["before_sar"] = {"url": url, "date": date}

    print(f"[imagery_fetcher] Fetching after true-colour ({window_start} to {window_end})...")
    url, date = get_s2_truecolor_thumbnail(bbox, window_start, window_end)
    cache["after_truecolor"] = {"url": url, "date": date}

    print(f"[imagery_fetcher] Fetching after NDWI...")
    url, date = get_s2_ndwi_thumbnail(bbox, window_start, window_end)
    cache["after_ndwi"] = {"url": url, "date": date}

    print(f"[imagery_fetcher] Fetching after SAR...")
    url, date = get_s1_sar_thumbnail(bbox, window_start, window_end)
    cache["after_sar"] = {"url": url, "date": date}

    print(f"[imagery_fetcher] Computing SAR log-ratio change detection...")
    url, period = get_s1_logratio_thumbnail(
        bbox, baseline_start, baseline_end, window_start, window_end
    )
    cache["logratio"] = {"url": url, "period": period}

    full_start = baseline_start
    full_end = window_end

    print(f"[imagery_fetcher] Building Sentinel-2 time-series strip ({full_start} to {full_end})...")
    cache["timeseries_s2"] = get_timeseries_thumbnails(
        bbox, full_start, full_end, num_images=8, image_type="S2_truecolor", dimensions=256
    )

    print(f"[imagery_fetcher] Building Sentinel-1 SAR time-series strip...")
    cache["timeseries_s1"] = get_timeseries_thumbnails(
        bbox, full_start, full_end, num_images=8, image_type="S1_SAR", dimensions=256
    )

    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)

    print(f"[imagery_fetcher] Cached imagery for {segment_id} -> {cache_path}")
    return cache
