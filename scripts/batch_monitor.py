#!/usr/bin/env python3
"""
batch_monitor.py — Automated statewide monitoring.

This script replaces the single-segment backtest by iterating over all
discovered segments in data/segments/*.geojson. For each segment, it:
1. Builds a seasonal baseline if one doesn't exist.
2. Runs the SAR anomaly detection for the last 30 days.
3. Scores the pass.
4. Appends the result to the global anomaly cache.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import ee

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.gee_auth import init_ee
from pipeline.sar_anomaly import build_reference_image, detect_anomaly, reduce_stats
from pipeline.ndwi_baseline import get_ndwi_image, get_sandbar_area_sq_m
from pipeline.seasonal_baseline_builder import load_baseline, build_segment_baseline
from pipeline.anomaly_scorer import score_pass
from pipeline.export_evidence_card import build_evidence_card, save_evidence_card

SEGMENTS_DIR = PROJECT_ROOT / "data" / "segments"
CACHE_PATH = PROJECT_ROOT / "data" / "anomaly_cache.json"

def geojson_to_ee_geometry(segment: dict):
    return ee.Geometry(segment["geometry"])

def run_batch_monitor(days_back: int = 30):
    init_ee()

    segments = list(SEGMENTS_DIR.glob("segment_*.geojson"))
    print(f"Found {len(segments)} segments to monitor.")

    if CACHE_PATH.exists():
        with open(CACHE_PATH) as f:
            cache = json.load(f)
    else:
        cache = {"updated_at": None, "segments": {}}

    today = datetime.now(timezone.utc)
    target_date = today.strftime("%Y-%m-%d")

    for seg_path in segments:
        with open(seg_path) as f:
            segment = json.load(f)
        
        segment_id = segment["properties"]["segment_id"]
        print(f"\nProcessing {segment_id}...")

        aoi = geojson_to_ee_geometry(segment)

        # Baseline check
        baseline = load_baseline(segment_id)
        if baseline is None:
            print(f"  Building seasonal baseline for {segment_id}...")
            try:
                baseline = build_segment_baseline(segment_id, aoi)
            except Exception as e:
                print(f"  Failed to build baseline: {e}")
                continue
        
        # SAR reference image
        ref_end = (today - timedelta(days=10)).strftime("%Y-%m-%d")
        ref_start = (today - timedelta(days=60)).strftime("%Y-%m-%d")
        reference_image = build_reference_image(aoi, ref_start, ref_end)

        # SAR detection
        try:
            sar_result = detect_anomaly(segment_id, aoi, target_date, reference_image, window_days=15)
            sar_result = reduce_stats(sar_result, aoi)
            print(f"  SAR: flagged_area={sar_result.flagged_area_sq_m} sq.m")
        except Exception as e:
            print(f"  SAR failed: {e}")
            sar_result = None

        # NDWI check
        try:
            ndwi_img = get_ndwi_image(
                aoi,
                (today - timedelta(days=10)).strftime("%Y-%m-%d"),
                (today + timedelta(days=10)).strftime("%Y-%m-%d"),
            )
            sandbar_area = get_sandbar_area_sq_m(aoi, ndwi_img)
            print(f"  NDWI area: {sandbar_area} sq.m")
        except Exception as e:
            print(f"  NDWI failed: {e}")
            sandbar_area = None
        
        # Score
        score = score_pass(
            segment_id=segment_id,
            pass_date=target_date,
            sar_result=sar_result,
            baseline=baseline,
            observed_sandbar_sq_m=sandbar_area,
            last_sar_pass=target_date,
            last_optical_pass=target_date,
        )

        print(f"  Result: {score.label} ({score.level.value})")

        cache["segments"][segment_id] = {
            "level": score.level.value,
            "label": score.label,
            "pass_date": score.pass_date,
            "coordinates": segment["geometry"]["coordinates"][0][0] if segment["geometry"]["type"] == "Polygon" else None,
            "river": segment["properties"].get("river", "Unknown")
        }

    cache["updated_at"] = today.isoformat()
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)
    
    print(f"\nMonitoring complete! Cache written to {CACHE_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch monitor all discovered segments.")
    parser.add_argument("--days", type=int, default=30, help="Days back to monitor")
    args = parser.parse_args()
    
    run_batch_monitor(args.days)
