#!/usr/bin/env python3
"""
backtest_case.py — runs the full detection pipeline against a documented
historical incident (spec Section 3, Phase 2).

Usage:
    python scripts/backtest_case.py --segment chambal_dholpur_morena --case case_001

This is the credibility anchor for the entire project. It:
  1. Loads the segment AOI and the case's documented incident window
  2. Builds (or loads cached) seasonal baseline for the segment
  3. Builds a SAR reference ("quiet baseline") image from a clean prior window
  4. Runs SAR anomaly detection + NDWI morphology check for the incident date
  5. Scores the result via anomaly_scorer
  6. Prints a pass/fail-style summary against the documented incident date
  7. On success, updates the case's metadata.json status (manual review still
     required before flipping to VERIFIED -- see Phase 2 checklist in spec)

Requires Earth Engine auth to be configured (see pipeline/gee_auth.py) and a
free Earth Engine account/project. This script will not run successfully in
an environment without network access to Earth Engine and a registered
project -- that's expected; it's meant to be run locally or in CI with
credentials configured, not inside this scaffold's sandbox.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

SEGMENTS_DIR = PROJECT_ROOT / "data" / "segments"
CASE_FILES_DIR = PROJECT_ROOT / "data" / "case_files"


def load_segment(segment_id: str) -> dict:
    path = SEGMENTS_DIR / f"segment_{segment_id}.geojson"
    if not path.exists():
        raise SystemExit(f"Segment file not found: {path}")
    with open(path) as f:
        return json.load(f)


def load_case(case_id: str) -> dict:
    path = CASE_FILES_DIR / case_id / "metadata.json"
    if not path.exists():
        raise SystemExit(f"Case file not found: {path}")
    with open(path) as f:
        return json.load(f)


def geojson_to_ee_geometry(segment: dict):
    import ee

    return ee.Geometry(segment["geometry"])


def run_backtest(segment_id: str, case_id: str, reference_days_before: int = 60) -> None:
    from pipeline.gee_auth import init_ee, EarthEngineAuthError
    from pipeline.sar_anomaly import build_reference_image, detect_anomaly, reduce_stats
    from pipeline.ndwi_baseline import get_ndwi_image, get_sandbar_area_sq_m
    from pipeline.seasonal_baseline_builder import load_baseline, build_segment_baseline
    from pipeline.anomaly_scorer import score_pass
    from pipeline.export_evidence_card import build_evidence_card, save_evidence_card

    segment = load_segment(segment_id)
    case = load_case(case_id)

    incident_date = case["incident_window"]["observed_activity_date"]
    print(f"== River Watch backtest: segment={segment_id} case={case_id} ==")
    print(f"Documented incident date: {incident_date}")

    try:
        init_ee()
    except EarthEngineAuthError as e:
        print(f"\nEarth Engine not available in this environment: {e}")
        print(
            "This is expected if you haven't run `earthengine authenticate` or "
            "configured a service account. Set that up locally / in CI to run "
            "the real backtest."
        )
        sys.exit(1)

    aoi = geojson_to_ee_geometry(segment)

    incident_dt = datetime.strptime(incident_date, "%Y-%m-%d")
    ref_end = (incident_dt - timedelta(days=10)).strftime("%Y-%m-%d")
    ref_start = (incident_dt - timedelta(days=reference_days_before)).strftime("%Y-%m-%d")

    print(f"Building SAR reference image: {ref_start} to {ref_end}")
    reference_image = build_reference_image(aoi, ref_start, ref_end)

    print("Running SAR anomaly detection for the incident window...")
    sar_result = detect_anomaly(segment_id, aoi, incident_date, reference_image, window_days=15)
    sar_result = reduce_stats(sar_result, aoi)
    print(
        f"  SAR: flagged_area={sar_result.flagged_area_sq_m} sq.m, "
        f"peak_log_ratio={sar_result.peak_log_ratio_db} dB"
    )

    print("Checking sandbar morphology against seasonal baseline...")
    baseline = load_baseline(segment_id)
    if baseline is None:
        print("  No cached baseline found -- building one now (this takes a while)...")
        baseline = build_segment_baseline(segment_id, aoi)

    ndwi_img = get_ndwi_image(
        aoi,
        (incident_dt - timedelta(days=10)).strftime("%Y-%m-%d"),
        (incident_dt + timedelta(days=10)).strftime("%Y-%m-%d"),
    )
    sandbar_area = get_sandbar_area_sq_m(aoi, ndwi_img)
    print(f"  Observed sandbar area: {sandbar_area:,.0f} sq. m")

    score = score_pass(
        segment_id=segment_id,
        pass_date=incident_date,
        sar_result=sar_result,
        baseline=baseline,
        observed_sandbar_sq_m=sandbar_area,
        last_sar_pass=incident_date,
        last_optical_pass=incident_date,
    )

    print(f"\n== Result: {score.label} (level={score.level.value}) ==")

    card = build_evidence_card(
        card_id=case_id,
        score=score,
        source_citation=case["sources"][0]["title"] if case.get("sources") else None,
    )
    out_path = save_evidence_card(card, case_dir=str(CASE_FILES_DIR / case_id))
    print(f"Evidence Card written to: {out_path}")

    if score.level.value == "under_review":
        print(
            "\nAnomaly aligns with the documented incident window. This is a "
            "candidate for VERIFIED status -- but per spec Phase 2, do a manual "
            "review of the imagery/numbers before updating metadata.json's "
            "status field. Do not auto-flip to VERIFIED without human review."
        )
    else:
        print(
            "\nAnomaly did NOT clearly align with the documented incident window. "
            "Per spec Phase 2: diagnose before proceeding (wrong segment boundary? "
            "noisy vegetation? wrong date range?). Do not publish this as a "
            "verified Case File."
        )


def main():
    parser = argparse.ArgumentParser(description="Backtest a case file against the detection pipeline.")
    parser.add_argument("--segment", required=True, help="segment_id, e.g. chambal_dholpur_morena")
    parser.add_argument("--case", required=True, help="case_id, e.g. case_001")
    args = parser.parse_args()
    run_backtest(args.segment, args.case)


if __name__ == "__main__":
    main()
