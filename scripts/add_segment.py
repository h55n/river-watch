#!/usr/bin/env python3
"""
add_segment.py — CLI helper to register a new monitored river segment.

Usage:
    python scripts/add_segment.py \\
        --id ganga_kanpur \\
        --name "Ganga River — near Kanpur" \\
        --river Ganga \\
        --states "Uttar Pradesh" \\
        --bbox 80.25 26.40 80.45 26.55 \\
        --notes "Coarse bounding box, refine before treating as final."

This writes data/segments/segment_<id>.geojson in the same format used
throughout the pipeline (see existing segment files for reference). It does
NOT automatically build a seasonal baseline or run a backtest -- those are
separate, deliberate steps (spec Phase 0 -> Phase 1 -> Phase 2), since
building a 5-year seasonal baseline costs real Earth Engine quota/time and
shouldn't happen silently as a side effect of registration.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone

SEGMENTS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "segments")


def main():
    parser = argparse.ArgumentParser(description="Register a new river segment.")
    parser.add_argument("--id", required=True, help="segment_id, lowercase_with_underscores")
    parser.add_argument("--name", required=True, help="Human-readable display name")
    parser.add_argument("--river", required=True, help="River name")
    parser.add_argument("--states", required=True, help="Comma-separated state names")
    parser.add_argument(
        "--bbox",
        required=True,
        nargs=4,
        type=float,
        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"),
        help="Bounding box in degrees: min_lon min_lat max_lon max_lat",
    )
    parser.add_argument("--protected-area", default=None, help="Protected area name, if any")
    parser.add_argument(
        "--notes",
        default="",
        help="Any caveats, e.g. ground-truth status, bounding box precision",
    )
    parser.add_argument(
        "--source-for-incident",
        default=None,
        help="If this segment is tied to a known documented incident, cite it here",
    )
    args = parser.parse_args()

    min_lon, min_lat, max_lon, max_lat = args.bbox
    if not (min_lon < max_lon and min_lat < max_lat):
        raise SystemExit("Invalid bbox: expected min_lon < max_lon and min_lat < max_lat")

    feature = {
        "type": "Feature",
        "properties": {
            "segment_id": args.id,
            "display_name": args.name,
            "river": args.river,
            "states": [s.strip() for s in args.states.split(",")],
            "protected_area": args.protected_area,
            "notes": args.notes,
            "source_for_incident": args.source_for_incident,
            "registered_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "status": "candidate_for_phase0_validation",
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [min_lon, min_lat],
                    [max_lon, min_lat],
                    [max_lon, max_lat],
                    [min_lon, max_lat],
                    [min_lon, min_lat],
                ]
            ],
        },
    }

    os.makedirs(SEGMENTS_DIR, exist_ok=True)
    out_path = os.path.join(SEGMENTS_DIR, f"segment_{args.id}.geojson")
    if os.path.exists(out_path):
        raise SystemExit(f"Segment already exists: {out_path}. Edit it directly instead.")

    with open(out_path, "w") as f:
        json.dump(feature, f, indent=2)

    print(f"Registered segment '{args.id}' -> {out_path}")
    print(
        "Next steps: validate the bbox against the actual river centerline, "
        "then build a seasonal baseline (pipeline.seasonal_baseline_builder."
        "build_segment_baseline) before this segment can be assessed for "
        "anomalies."
    )


if __name__ == "__main__":
    main()
