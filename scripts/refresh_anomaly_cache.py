#!/usr/bin/env python3
"""
refresh_anomaly_cache.py — computes the current anomaly level for the
chambal_001 vital segment and writes:

  data/anomaly_cache.json           — anomaly level (read by Streamlit on page load)
  data/baselines/baseline_chambal_001.json  — structured anomaly score with GEE values
  data/imagery_cache/chambal_001_imagery.json — GEE thumbnail URLs for the UI

Why this exists: querying Earth Engine live on every Streamlit page load
would be slow, expensive against free-tier quota, and would hammer GEE with
duplicate work every time a visitor refreshes the map. Instead, this script
is meant to be run on a schedule (e.g. a daily/weekly GitHub Actions cron
job, since Sentinel-1/2 only revisit every few days anyway -- see spec
Section 2.3) and the app just reads the cached result.

Run order (do NOT re-order):
  1. GEE init
  2. Load segment chambal_001
  3. Compute anomaly score -> write baseline_chambal_001.json
  4. Cache imagery URLs -> write chambal_001_imagery.json
  5. Update anomaly_cache.json
  6. Print completion summary with timestamp

Usage:
    python scripts/refresh_anomaly_cache.py

Requires Earth Engine auth (see pipeline/gee_auth.py). Will not produce
useful output without it.

IMPORTANT: This script must NEVER be called from within the Streamlit app
at runtime. It is a scheduled offline pipeline job only.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

SEGMENTS_DIR = PROJECT_ROOT / "data" / "segments"
CACHE_PATH = PROJECT_ROOT / "data" / "anomaly_cache.json"
BASELINES_DIR = PROJECT_ROOT / "data" / "baselines"
IMAGERY_CACHE_DIR = PROJECT_ROOT / "data" / "imagery_cache"

# The ONE vital segment for Phase 1 validation
VITAL_SEGMENT_ID = "chambal_001"
VITAL_SEGMENT_FILE = SEGMENTS_DIR / f"segment_{VITAL_SEGMENT_ID}.geojson"


def load_segment(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def refresh():
    from pipeline.gee_auth import init_ee, EarthEngineAuthError
    from pipeline.sar_anomaly import build_reference_image, detect_anomaly, reduce_stats
    from pipeline.ndwi_baseline import get_ndwi_image, get_sandbar_area_sq_m
    from pipeline.seasonal_baseline_builder import load_baseline
    from pipeline.anomaly_scorer import score_pass
    from pipeline.imagery_fetcher import cache_imagery_for_segment

    # ── 1. GEE Init ──────────────────────────────────────────────────────────
    print("[refresh] Initialising Earth Engine...")
    try:
        init_ee()
    except EarthEngineAuthError as e:
        print(f"Earth Engine not available: {e}", file=sys.stderr)
        print(
            "Cannot refresh the live anomaly cache without Earth Engine access. "
            "The app will fall back to showing 'insufficient data' until this "
            "is run successfully at least once.",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── 2. Load chambal_001 segment ──────────────────────────────────────────
    if not VITAL_SEGMENT_FILE.exists():
        print(f"[refresh] FATAL: {VITAL_SEGMENT_FILE} not found.", file=sys.stderr)
        sys.exit(1)

    print(f"[refresh] Loading segment {VITAL_SEGMENT_ID}...")
    seg = load_segment(VITAL_SEGMENT_FILE)
    props = seg["properties"]
    seg_id = props["segment_id"]

    import ee
    aoi = ee.Geometry(seg["geometry"])

    # Use the segment's defined analysis windows, not rolling today-based windows
    # (this preserves reproducibility — we're backtesting a known incident window)
    baseline_start = props.get("baseline_start", "2022-06-01")
    baseline_end = props.get("baseline_end", "2022-12-15")
    window_start = props.get("incident_window_start", "2022-12-20")
    window_end = props.get("incident_window_end", "2023-01-20")
    pass_date = props.get("incident_date", "2023-01-01")

    print(f"  Baseline: {baseline_start} to {baseline_end}")
    print(f"  Incident window: {window_start} to {window_end}")

    # ── 3. Compute anomaly score ─────────────────────────────────────────────
    print(f"[refresh] Running SAR anomaly detection...")
    results = {}
    anomaly_score_dict = {}

    try:
        reference_image = build_reference_image(aoi, baseline_start, baseline_end)
        sar_result = detect_anomaly(seg_id, aoi, pass_date, reference_image, window_days=15)
        sar_result = reduce_stats(sar_result, aoi, scale=30)

        baseline = load_baseline(seg_id)
        ndwi_img = get_ndwi_image(aoi, window_start, window_end)
        sandbar_area = get_sandbar_area_sq_m(aoi, ndwi_img)

        # Get baseline NDWI for comparison
        baseline_ndwi_img = get_ndwi_image(aoi, baseline_start, baseline_end)
        baseline_sandbar_area = get_sandbar_area_sq_m(aoi, baseline_ndwi_img)

        score = score_pass(
            segment_id=seg_id,
            pass_date=pass_date,
            sar_result=sar_result,
            baseline=baseline,
            observed_sandbar_sq_m=sandbar_area,
            last_sar_pass=window_end,
            last_optical_pass=window_end,
        )

        # Compute NDWI change pct vs baseline
        ndwi_change_pct = None
        if baseline_sandbar_area and sandbar_area is not None:
            ndwi_change_pct = round(
                (sandbar_area - baseline_sandbar_area) / baseline_sandbar_area * 100, 1
            )

        # Compute combined score (0.0-1.0) — heuristic, not a calibrated model
        sar_flag = sar_result.peak_log_ratio_db is not None and sar_result.peak_log_ratio_db > 3.0
        ndwi_flag = ndwi_change_pct is not None and abs(ndwi_change_pct) > 10
        combined_score = round(
            (0.6 if sar_flag else 0.0) + (0.4 if ndwi_flag else 0.0), 2
        )
        confidence = (
            "high" if (sar_flag and ndwi_flag)
            else "medium" if (sar_flag or ndwi_flag)
            else "low"
        )

        # Count available passes for data quality note
        s1_count = (
            ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterBounds(aoi)
            .filterDate(window_start, window_end)
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .size()
            .getInfo()
        )
        s2_count = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(aoi)
            .filterDate(window_start, window_end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
            .size()
            .getInfo()
        )

        # Build structured anomaly score dict (spec schema)
        anomaly_score_dict = {
            "segment_id": seg_id,
            "computed_at": datetime.now(timezone.utc).isoformat() + "Z",
            "status": "anomaly_detected" if (sar_flag or ndwi_flag) else "within_baseline",
            "hedge_label": "Anomaly detected \u2014 under review",
            "sar_logratio_delta": round(sar_result.peak_log_ratio_db, 2) if sar_result.peak_log_ratio_db else None,
            "sar_anomaly_flag": sar_flag,
            "ndwi_area_change_pct": ndwi_change_pct,
            "ndwi_anomaly_flag": ndwi_flag,
            "combined_score": combined_score,
            "confidence": confidence,
            "baseline_period": f"{baseline_start} to {baseline_end}",
            "analysis_period": f"{window_start} to {window_end}",
            "data_quality_notes": f"{s1_count} S1 pass(es), {s2_count} S2 clear pass(es) in incident window",
            "seasonal_baseline_sandbar_sq_m": baseline_sandbar_area,
            "incident_sandbar_sq_m": sandbar_area,
        }

        # Persist anomaly score
        BASELINES_DIR.mkdir(parents=True, exist_ok=True)
        baseline_out_path = BASELINES_DIR / f"baseline_{seg_id}.json"
        with open(baseline_out_path, "w") as f:
            json.dump(anomaly_score_dict, f, indent=2)
        print(f"  -> Anomaly score written to {baseline_out_path}")
        print(f"  -> Level: {score.level.value} | SAR flag: {sar_flag} | NDWI flag: {ndwi_flag} | Combined: {combined_score}")

        results[seg_id] = {
            "level": score.level.value,
            "label": score.label,
            "hedge_label": anomaly_score_dict["hedge_label"],
            "combined_score": combined_score,
            "confidence": confidence,
            "sar_logratio_delta": anomaly_score_dict["sar_logratio_delta"],
            "ndwi_area_change_pct": ndwi_change_pct,
            "last_checked": datetime.now(timezone.utc).isoformat() + "Z",
        }

    except Exception as exc:
        print(f"  FAILED anomaly scoring for {seg_id}: {exc}", file=sys.stderr)
        results[seg_id] = {
            "level": "low",
            "label": "Insufficient data this pass \u2014 anomaly status not assessable",
            "last_checked": datetime.now(timezone.utc).isoformat() + "Z",
            "error": str(exc),
        }

    # ── 4. Cache imagery URLs ─────────────────────────────────────────────────
    print(f"\n[refresh] Caching imagery thumbnails for {seg_id}...")
    IMAGERY_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    imagery_cache_path = IMAGERY_CACHE_DIR / f"{seg_id}_imagery.json"

    try:
        cache_imagery_for_segment(
            segment_id=seg_id,
            segment_meta=props,
            cache_path=str(imagery_cache_path),
        )
        print(f"  -> Imagery cache written to {imagery_cache_path}")
    except Exception as exc:
        print(f"  FAILED imagery caching for {seg_id}: {exc}", file=sys.stderr)
        # Write empty cache so the UI can show a proper warning
        empty_cache = {
            "segment_id": seg_id,
            "generated_at": datetime.now(timezone.utc).isoformat() + "Z",
            "error": str(exc),
            "before_truecolor": {"url": None, "date": None},
            "after_truecolor": {"url": None, "date": None},
            "before_ndwi": {"url": None, "date": None},
            "after_ndwi": {"url": None, "date": None},
            "before_sar": {"url": None, "date": None},
            "after_sar": {"url": None, "date": None},
            "logratio": {"url": None, "period": None},
            "timeseries_s2": [],
            "timeseries_s1": [],
        }
        with open(imagery_cache_path, "w") as f:
            json.dump(empty_cache, f, indent=2)

    # ── 5. Write anomaly_cache.json ───────────────────────────────────────────
    generated_at = datetime.now(timezone.utc).isoformat() + "Z"
    with open(CACHE_PATH, "w") as f:
        json.dump(
            {"generated_at": generated_at, "segments": results},
            f,
            indent=2,
        )
    print(f"\n[refresh] anomaly_cache.json written to {CACHE_PATH}")

    # ── 6. Summary ────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"Cache refresh complete.")
    print(f"Last updated: {generated_at}")
    print(f"Segment processed: {seg_id}")
    print(f"Files written:")
    print(f"  {CACHE_PATH}")
    print(f"  {BASELINES_DIR / f'baseline_{seg_id}.json'}")
    print(f"  {IMAGERY_CACHE_DIR / f'{seg_id}_imagery.json'}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    refresh()
