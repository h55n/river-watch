"""
map_view.py — Folium-based map rendering for monitored river segments,
anomaly flags, and supplementary FIRMS/GFW layers.

Used by both Tier 1 (Anomaly Watch) and Tier 2 (Case Files) pages.
"""

from __future__ import annotations

import json
import os
from typing import List, Optional

import folium

SEGMENTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "segments")

ANOMALY_COLORS = {
    "none": "#3a7d44",  # quiet green
    "low": "#9c9c9c",  # neutral grey -- insufficient data, not "safe"
    "elevated": "#e0a32e",  # amber
    "under_review": "#c1440e",  # flagged, hedged red-orange (never pure alarm red)
}


def load_all_segments() -> List[dict]:
    """
    Load every active segment GeoJSON file under data/segments/.
    Archived files (.geojson.archived) are skipped.
    Phase 1: only segment_chambal_001.geojson is active.
    """
    segments = []
    if not os.path.isdir(SEGMENTS_DIR):
        return segments
    for fname in sorted(os.listdir(SEGMENTS_DIR)):
        if fname.endswith(".geojson") and not fname.endswith(".archived"):
            with open(os.path.join(SEGMENTS_DIR, fname)) as f:
                segments.append(json.load(f))
    return segments


def build_segment_map(
    segments: Optional[List[dict]] = None,
    anomaly_levels: Optional[dict] = None,
    firms_points: Optional[list] = None,
    center: tuple = (26.725, 77.9),  # Chambal centre (Phase 1 default)
    zoom_start: int = 10,
) -> folium.Map:
    """
    Build a Folium map with all active monitored segments, colored by current
    anomaly level (spec Section 5.1), plus optional FIRMS thermal points
    as a clearly-separate supplementary layer.

    FIRMS/GFW are reference layers ONLY — not River Watch's mining detection.
    They must be clearly labelled as such in the layer control.

    anomaly_levels: dict of {segment_id: level_str} where level_str is one of
        "none" / "low" / "elevated" / "under_review". Segments without an
        entry render in the "low" / neutral-grey color (insufficient data),
        never defaulted to green ("none") -- absence of data is not absence
        of an anomaly.
    """
    segments = segments if segments is not None else load_all_segments()
    anomaly_levels = anomaly_levels or {}

    fmap = folium.Map(location=center, zoom_start=zoom_start, tiles=None)

    # Stadia dark basemap — works without API key via Folium's built-in support
    folium.TileLayer(
        tiles="https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png",
        attr="&copy; Stadia Maps &copy; OpenMapTiles &copy; OpenStreetMap contributors",
        name="Stadia Alidade Dark",
        max_zoom=20,
    ).add_to(fmap)

    segment_layer = folium.FeatureGroup(name="Monitored river segments", show=True)
    for seg in segments:
        seg_id = seg["properties"].get("segment_id", "unknown")
        level = anomaly_levels.get(seg_id, "low")
        color = ANOMALY_COLORS.get(level, ANOMALY_COLORS["low"])
        display_name = seg["properties"].get("display_name", seg_id)
        ngt_ref = seg["properties"].get("ngt_case_ref", "")

        popup_html = (
            f"<b>{display_name}</b><br>"
            f"Status: {level.replace('_', ' ').title()}<br>"
            f"{f'NGT Ref: {ngt_ref}<br>' if ngt_ref else ''}"
            f"<i>Anomaly flag — not a confirmation. See Case Files for verified examples.</i>"
        )

        folium.GeoJson(
            seg,
            style_function=lambda _f, color=color: {
                "fillColor": color,
                "color": color,
                "weight": 2,
                "fillOpacity": 0.25,
            },
            tooltip=display_name,
            popup=folium.Popup(popup_html, max_width=300),
        ).add_to(segment_layer)
    segment_layer.add_to(fmap)

    if firms_points:
        firms_layer = folium.FeatureGroup(
            name="🔥 NASA FIRMS thermal anomalies (fires/kilns — NOT mining detection)",
            show=False,
        )
        for pt in firms_points:
            folium.CircleMarker(
                location=(pt.latitude, pt.longitude),
                radius=4,
                color="#d62828",
                fill=True,
                fill_opacity=0.7,
                popup=(
                    f"Thermal anomaly — {pt.acq_date} {pt.acq_time}\n"
                    f"Source: NASA FIRMS (fires/industrial heat — reference only, not mining confirmation)"
                ),
            ).add_to(firms_layer)
        firms_layer.add_to(fmap)

    folium.LayerControl(collapsed=False).add_to(fmap)
    return fmap
