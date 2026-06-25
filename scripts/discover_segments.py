#!/usr/bin/env python3
"""
discover_segments.py — Automated discovery of river sandbars for statewide monitoring.

This script uses Earth Engine to:
1. Load a target state boundary (e.g., Rajasthan, India).
2. Constrain the search area to major river channels using JRC Global Surface Water (max extent).
3. Identify exposed sandbars within the river channels using a dry-season optical composite (Sentinel-2).
4. Vectorize the sandbars and generate monitoring segment AOIs.
5. Save the segments to data/segments/ for batch monitoring.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import ee

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.gee_auth import init_ee

SEGMENTS_DIR = PROJECT_ROOT / "data" / "segments"


def discover_and_export(state_name: str, max_segments: int = 50):
    print(f"Initializing Earth Engine and authenticating...")
    init_ee()

    print(f"Loading boundary for state: {state_name}")
    # Get state boundary from FAO GAUL dataset
    states = ee.FeatureCollection("FAO/GAUL/2015/level1")
    target_state = states.filter(ee.Filter.eq("ADM1_NAME", state_name))

    # Check if state exists
    if target_state.size().getInfo() == 0:
        print(f"Error: State '{state_name}' not found in FAO GAUL dataset.")
        sys.exit(1)

    state_geom = target_state.geometry()

    print("Fetching JRC Global Surface Water to mask major river channels...")
    # JRC Max Water Extent (where water has EVER been detected)
    jrc = ee.Image("JRC/GSW1_4/GlobalSurfaceWater")
    max_extent = jrc.select("max_extent").eq(1)

    # We want a dry-season composite to find exposed sandbars inside the max water extent
    print("Building dry-season Sentinel-2 composite (Nov - Feb)...")
    s2 = ee.ImageCollection("COPERNICUS/S2_HARMONIZED") \
        .filterBounds(state_geom) \
        .filterDate("2023-11-01", "2024-02-28") \
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 10))

    if s2.size().getInfo() == 0:
         print("No Sentinel-2 imagery found for the specified period.")
         sys.exit(1)

    median_s2 = s2.median()

    # Calculate NDWI: (Green - NIR) / (Green + NIR)
    # Sentinel-2 bands: Green = B3, NIR = B8
    ndwi = median_s2.normalizedDifference(["B3", "B8"])

    # Water is > 0, sand/soil is < 0. We want exposed sandbars (NDWI < 0) inside the river channel
    is_sandbar = ndwi.lt(0).And(max_extent)

    print("Extracting sandbar polygons and filtering by size...")
    # Mask out non-sandbar pixels
    sandbar_mask = is_sandbar.updateMask(is_sandbar)

    # Vectorize
    # To avoid hitting memory limits, we'll scale it up (e.g. 100m instead of 10m)
    # and restrict maxPixels.
    vectors = sandbar_mask.reduceToVectors(
        geometry=state_geom,
        crs=ndwi.projection(),
        scale=100, # 100m scale for statewide processing to avoid memory limits
        geometryType="polygon",
        eightConnected=True,
        maxPixels=1e10
    )

    # Filter out tiny sandbars. Area is in square meters.
    # 100,000 sq meters = 0.1 sq km = 10 hectares. Good size for equipment.
    large_sandbars = vectors.filter(ee.Filter.gt("count", 10)) # 10 pixels at 100x100m = 100,000 sqm

    # Limit to top N largest or just take a sample to avoid overloading
    # Sorting by count (area) descending
    top_sandbars = large_sandbars.sort("count", False).limit(max_segments)

    # Fetch features
    features = top_sandbars.getInfo()["features"]

    print(f"Found {len(features)} significant sandbar segments in {state_name}.")
    
    os.makedirs(SEGMENTS_DIR, exist_ok=True)

    for i, feat in enumerate(features):
        segment_id = f"auto_{state_name.lower().replace(' ', '_')}_{i:03d}"
        
        # Buffer the polygon slightly (e.g. 500m) to capture equipment near the bank
        # We do this client side with a simplified bounding box or GEE buffer.
        # It's easier to buffer in GEE before downloading, but since we already have the raw geojson,
        # we'll just save it. The anomaly pipeline will analyze this AOI.

        # Simplify the geometry to avoid massive files
        geom = ee.Geometry(feat["geometry"]).simplify(maxError=50)
        simplified_geojson = geom.getInfo()

        segment_data = {
            "type": "Feature",
            "properties": {
                "segment_id": segment_id,
                "display_name": f"Automated Segment {i} - {state_name}",
                "river": "Unknown (Automated)",
                "states": [state_name],
                "protected_area": "Unknown",
                "notes": "Automatically discovered sandbar via NDWI / JRC water mask.",
                "boundary_method": "Automated S2 NDWI < 0 within JRC Max Extent",
                "boundary_version": "v1-auto",
                "registered_date": "2026-06-21",
                "status": "candidate_for_monitoring",
            },
            "geometry": simplified_geojson
        }

        path = SEGMENTS_DIR / f"segment_{segment_id}.geojson"
        with open(path, "w") as f:
            json.dump(segment_data, f, indent=2)
        
        print(f"  Saved {path.name}")

    print("Discovery complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Discover sandbar segments for a given state.")
    parser.add_argument("--state", required=True, help="State name (e.g. Rajasthan)")
    parser.add_argument("--limit", type=int, default=20, help="Max number of segments to discover")
    args = parser.parse_args()
    
    discover_and_export(args.state, args.limit)
