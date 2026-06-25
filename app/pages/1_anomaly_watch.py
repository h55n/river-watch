"""
1_anomaly_watch.py — Tier 1: Anomaly Watch.

Chambal River (Dholpur/Morena) vital segment monitoring.
Loads cached GEE data — NEVER calls Earth Engine at page-load time.

All imagery: Copernicus Sentinel data (ESA), open licence.
Processed via Google Earth Engine (offline pipeline).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import folium
import streamlit as st
from streamlit_folium import st_folium

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.components.load_css import load_css

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ANOMALY_CACHE_PATH = PROJECT_ROOT / "data" / "anomaly_cache.json"
IMAGERY_CACHE_PATH = PROJECT_ROOT / "data" / "imagery_cache" / "chambal_001_imagery.json"
SEGMENT_DIR = PROJECT_ROOT / "data" / "segments"
BASELINE_SCORE_PATH = PROJECT_ROOT / "data" / "baselines" / "baseline_chambal_001.json"
DASHBOARD_PATH = PROJECT_ROOT / "data" / "dashboard.json"

CHAMBAL_CENTER = [26.725, 77.9]
ALL_SEGMENTS_CENTER = [27.5, 78.5]

st.set_page_config(
    page_title="River Watch — Anomaly Watch",
    page_icon="🛰️",
    layout="wide",
)
load_css()


def load_json_cache(path: Path) -> dict | None:
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🛰️ Anomaly Watch")
st.markdown(
    "**Sentinel-1 SAR + Sentinel-2 optical monitoring — "
    "Chambal River (Dholpur/Morena)**"
)

# Last refreshed timestamp
anomaly_cache = load_json_cache(ANOMALY_CACHE_PATH)
last_refreshed = anomaly_cache.get("generated_at", "unknown") if anomaly_cache else "never"
st.markdown(
    f'<span class="rw-mono">Cache last refreshed: {last_refreshed[:19].replace("T", " ")} UTC</span>',
    unsafe_allow_html=True,
)

# Hedge notice (required)
st.markdown("""
<div class="rw-hedge-notice">
  Anomaly Watch flags statistical deviations from seasonal baselines.
  A flag means "worth investigating," never "confirmed illegal."
  All imagery is from the Copernicus programme (ESA), used under open licence.
  Every flag requires human review — legal, journalistic, or on-ground — before any conclusion is drawn.
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="rw-divider">', unsafe_allow_html=True)

# ── Check if caches exist ─────────────────────────────────────────────────────
imagery_cache = load_json_cache(IMAGERY_CACHE_PATH)
baseline_score = load_json_cache(BASELINE_SCORE_PATH)
dashboard = load_json_cache(DASHBOARD_PATH)

if not anomaly_cache or not imagery_cache:
    st.warning(
        "⚠️ **No anomaly cache found.** "
        "Run `python scripts/refresh_anomaly_cache.py` with Earth Engine "
        "credentials to generate satellite data. "
        "The map and imagery below will be empty until then.",
        icon=None,
    )

# ── All monitored segments map ────────────────────────────────────────────────
st.markdown("### 📍 All Monitored Segments")
st.markdown(
    '<span class="rw-mono">4 river stretches monitored · '
    'Chambal GEE-validated · Yamuna/Ken/Ganga NGT-corroborated (imagery pending GEE run)</span>',
    unsafe_allow_html=True,
)

# Build Folium map with all segments
fmap = folium.Map(
    location=ALL_SEGMENTS_CENTER,
    zoom_start=6,
    tiles=None,
)
folium.TileLayer(
    tiles="https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png",
    attr="&copy; Stadia Maps &copy; OpenMapTiles &copy; OpenStreetMap contributors",
    name="Stadia Alidade Dark",
    max_zoom=20,
).add_to(fmap)

# Load all segment GeoJSON files
level_colors = {
    "under_review": "#ffd60a",
    "elevated": "#f77f00",
    "none": "#52b788",
    "low": "#8896b3",
}

# Build anomaly levels dict from cache
anomaly_levels = {}
if anomaly_cache:
    for seg_id, seg_data in anomaly_cache.get("segments", {}).items():
        anomaly_levels[seg_id] = seg_data.get("level", "low")

# Add all segments from dashboard
if dashboard:
    for hotspot in dashboard.get("hotspots", []):
        h_id = hotspot["id"]
        level = hotspot.get("anomaly_level", anomaly_levels.get(h_id, "low"))
        color = level_colors.get(level, "#8896b3")
        bbox = hotspot.get("bbox", [])
        lat, lon = hotspot["lat"], hotspot["lon"]
        is_gee = hotspot.get("data_source") == "gee_computed"

        if bbox:
            west, south, east, north = bbox
            popup_html = f"""
            <div style="font-family:sans-serif;min-width:220px">
              <b>{hotspot['name']}</b><br>
              <small>{hotspot['state']}</small><br><br>
              <b>Status:</b> {hotspot.get('hedge_label', level)}<br>
              <b>NGT Ref:</b> {hotspot.get('ngt_case_ref', '')}<br>
              <b>Data:</b> {'✓ GEE-Validated' if is_gee else '⏳ Imagery pending GEE run'}<br>
              <small><i>Anomaly flag — not a confirmation. Human review required.</i></small>
            </div>
            """

            folium.Rectangle(
                bounds=[[south, west], [north, east]],
                color=color,
                weight=2,
                fill=True,
                fill_color=color,
                fill_opacity=0.15,
                dash_array="6 4" if not is_gee else None,
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=hotspot["name"],
            ).add_to(fmap)

        # Centre marker
        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            popup=folium.Popup(
                f"<b>{hotspot['name']}</b><br>{level.replace('_', ' ').title()}<br>"
                f"<i>{'GEE-Validated' if is_gee else 'Imagery pending GEE run'}</i>",
                max_width=200,
            ),
            tooltip=hotspot["name"],
        ).add_to(fmap)

# FIRMS thermal layer
firms_api_key = os.environ.get("FIRMS_API_KEY", "")
firms_label = (
    "🔥 NASA FIRMS Thermal Anomalies (fires/kilns — not mining detection)"
    if firms_api_key
    else "🔥 NASA FIRMS Thermal Anomalies (API key not configured)"
)
firms_layer = folium.FeatureGroup(name=firms_label, show=False)
firms_layer.add_to(fmap)

# GFW reference layer
gfw_layer = folium.FeatureGroup(
    name="🌳 Global Forest Watch Alerts (credited reference layer — WRI/GFW)",
    show=False,
)
gfw_layer.add_to(fmap)

folium.LayerControl(collapsed=False).add_to(fmap)
st_folium(fmap, width=None, height=480)

# Legend
st.markdown("""
<div style="display:flex;gap:24px;padding:8px 0;font-size:12px;color:#8896b3">
  <span><span style="color:#f77f00">■</span> SAR Elevated</span>
  <span><span style="color:#ffd60a">■</span> Under Review</span>
  <span><span style="color:#52b788">■</span> Clear</span>
  <span><span style="color:#8896b3">■</span> Monitoring / Low data</span>
  <span style="opacity:0.6">- - dashed = imagery pending GEE run</span>
</div>
""", unsafe_allow_html=True)

if not firms_api_key:
    st.info(
        "📡 **NASA FIRMS Thermal Layer**: Add `FIRMS_API_KEY` to your `.env` file "
        "(free API key at https://firms.modaps.eosdis.nasa.gov/api/) to see live "
        "thermal anomaly overlays (fires/kilns — reference layer, not mining detection).",
        icon=None,
    )

st.markdown('<hr class="rw-divider">', unsafe_allow_html=True)

# ── Anomaly status strip ──────────────────────────────────────────────────────
st.markdown("### 📊 Anomaly Status — Chambal 001 (GEE-Validated)")

if not baseline_score and not anomaly_cache:
    st.info(
        "Run `python scripts/refresh_anomaly_cache.py` to compute "
        "actual SAR and NDWI values from Google Earth Engine.",
        icon="📡",
    )
else:
    sar_delta = None
    ndwi_change = None
    combined_score = None
    confidence = None
    sar_flag = False
    ndwi_flag = False

    if baseline_score:
        sar_delta = baseline_score.get("sar_logratio_delta")
        ndwi_change = baseline_score.get("ndwi_area_change_pct")
        combined_score = baseline_score.get("combined_score")
        confidence = baseline_score.get("confidence")
        sar_flag = baseline_score.get("sar_anomaly_flag", False)
        ndwi_flag = baseline_score.get("ndwi_anomaly_flag", False)
        data_quality = baseline_score.get("data_quality_notes", "")
        computed_at = baseline_score.get("computed_at", "")
    elif anomaly_cache:
        seg_data = anomaly_cache.get("segments", {}).get("chambal_001", {})
        sar_delta = seg_data.get("sar_logratio_delta")
        ndwi_change = seg_data.get("ndwi_area_change_pct")
        combined_score = seg_data.get("combined_score")
        confidence = seg_data.get("confidence")
        data_quality = ""
        computed_at = ""

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="rw-card">', unsafe_allow_html=True)
        if sar_delta is not None:
            flag_html = '<span class="rw-data-flag">▲ FLAGGED</span>' if sar_flag else '<span style="color:#52b788;font-size:11px">WITHIN RANGE</span>'
            st.markdown(
                f'<span class="rw-data-value">Δ {sar_delta:+.1f} dB</span>'
                f'<span class="rw-data-label">SAR Backscatter Change</span>'
                f'{flag_html}',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span class="rw-data-value" style="color:#4a5580">—</span>'
                '<span class="rw-data-label">SAR Backscatter Change</span>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="rw-card">', unsafe_allow_html=True)
        if ndwi_change is not None:
            flag_html = '<span class="rw-data-flag">▲ FLAGGED</span>' if ndwi_flag else '<span style="color:#52b788;font-size:11px">WITHIN RANGE</span>'
            st.markdown(
                f'<span class="rw-data-value">{ndwi_change:+.1f}%</span>'
                f'<span class="rw-data-label">NDWI Sandbar Area Change</span>'
                f'{flag_html}',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span class="rw-data-value" style="color:#4a5580">—</span>'
                '<span class="rw-data-label">NDWI Sandbar Area Change</span>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="rw-card">', unsafe_allow_html=True)
        if combined_score is not None:
            st.markdown(
                f'<span class="rw-data-value">{combined_score:.2f} / 1.0</span>'
                f'<span class="rw-data-label">Combined Score · Confidence: {confidence or "—"}</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span class="rw-data-value" style="color:#4a5580">—</span>'
                '<span class="rw-data-label">Combined Score</span>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    if baseline_score and baseline_score.get("data_quality_notes"):
        st.markdown(
            f'<span class="rw-mono">Data quality: {baseline_score["data_quality_notes"]}</span>',
            unsafe_allow_html=True,
        )

st.markdown('<hr class="rw-divider">', unsafe_allow_html=True)

# ── Real satellite imagery ────────────────────────────────────────────────────
st.markdown("### 🛰️ Satellite Imagery — Before & After Comparison")
st.markdown(
    '<p style="color:#8896b3;font-size:13px">'
    "All imagery: Copernicus Sentinel data (ESA), processed via Google Earth Engine. "
    "Acquisition dates shown below each image."
    "</p>",
    unsafe_allow_html=True,
)

if not imagery_cache:
    st.info(
        "📡 Imagery not yet cached. Run `python scripts/refresh_anomaly_cache.py` "
        "with Earth Engine credentials to generate satellite thumbnails.",
        icon=None,
    )
else:
    generated_at = imagery_cache.get("generated_at", "unknown")
    st.markdown(
        f'<span class="rw-mono">Imagery generated: {generated_at[:19].replace("T", " ")} UTC</span>',
        unsafe_allow_html=True,
    )

    def show_image(col, cache_key: str, label: str, period_label: str = ""):
        """Display a cached GEE thumbnail with proper labels."""
        entry = imagery_cache.get(cache_key, {})
        url = entry.get("url") if isinstance(entry, dict) else None
        date = entry.get("date") or entry.get("period") or period_label
        with col:
            if url:
                st.image(url, use_container_width=True)
                st.markdown(f'<div class="rw-sat-label">{label}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="rw-sat-date">{date}</div>', unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div style="background:#0a0e2a;border:1px solid #1a2040;border-radius:8px;'
                    f'padding:40px;text-align:center;color:#4a5580">'
                    f'<div style="font-size:28px">🛰️</div><div style="margin-top:8px">{label}</div>'
                    f'<div style="font-size:11px;margin-top:4px">Run refresh_anomaly_cache.py to populate</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

    # Row 1: True Colour before/after
    st.markdown("#### True Colour (RGB) — Sentinel-2")
    col_b1, col_a1 = st.columns(2)
    show_image(col_b1, "before_truecolor", "Sentinel-2 True Colour — BEFORE (Baseline · Oct 2022)")
    show_image(col_a1, "after_truecolor", "Sentinel-2 True Colour — AFTER (Incident Window · Jan 2023)")

    # Row 2: NDWI before/after
    st.markdown("#### Water / Sandbar Index (NDWI) — Sentinel-2")
    st.markdown(
        '<span class="rw-mono">Brown/wheat = exposed sandbar · Blue = water channel · '
        "Dark = vegetation</span>",
        unsafe_allow_html=True,
    )
    col_b2, col_a2 = st.columns(2)
    show_image(col_b2, "before_ndwi", "Sentinel-2 NDWI — BEFORE (Baseline)")
    show_image(col_a2, "after_ndwi", "Sentinel-2 NDWI — AFTER (Incident Window)")

    # Row 3: SAR before/after + logratio
    st.markdown("#### SAR Backscatter — Sentinel-1 (C-band, VV-polarization)")
    st.markdown(
        '<span class="rw-mono">Bright = high radar return (metal/equipment/water) · '
        "Dark = smooth surface (sand/calm water)</span>",
        unsafe_allow_html=True,
    )
    col_b3, col_a3, col_lr = st.columns(3)
    show_image(col_b3, "before_sar", "Sentinel-1 SAR VV — BEFORE (Baseline · Dec 2022)")
    show_image(col_a3, "after_sar", "Sentinel-1 SAR VV — AFTER (Incident Window · Jan 2023)")
    show_image(
        col_lr,
        "logratio",
        "SAR Log-Ratio Change Detection (Red = backscatter ↑, Blue = ↓)",
    )

    st.markdown("""
<div class="rw-hedge-notice">
  <strong>SAR log-ratio:</strong> Red/orange areas indicate increased backscatter vs. the baseline period.
  This <em>may</em> indicate equipment or vessel presence on the riverbed. It requires human review to confirm —
  other explanations (authorised activity, sensor geometry, surface moisture changes) are possible.
</div>
""", unsafe_allow_html=True)

    st.markdown('<hr class="rw-divider">', unsafe_allow_html=True)

    # ── Time-series pass strips ───────────────────────────────────────────────
    ts_s2 = imagery_cache.get("timeseries_s2", [])
    ts_s1 = imagery_cache.get("timeseries_s1", [])

    if ts_s2:
        st.markdown("#### 📡 Sentinel-2 Pass History (True Colour — Chambal Riverbed)")
        st.caption(
            f"Showing {len(ts_s2)} actual Sentinel-2 acquisitions over the "
            "Chambal monitoring segment, ordered chronologically. "
            "Each panel is a real satellite pass — not generated."
        )
        cols = st.columns(len(ts_s2))
        for i, entry in enumerate(ts_s2):
            with cols[i]:
                if entry.get("url"):
                    st.image(entry["url"], use_container_width=True)
                    st.markdown(
                        f'<div class="rw-sat-date" style="font-size:10px">{entry.get("date", "")}</div>',
                        unsafe_allow_html=True,
                    )
    else:
        st.markdown("#### 📡 Sentinel-2 Pass History")
        st.info("No time-series data yet. Run `refresh_anomaly_cache.py`.", icon=None)

    if ts_s1:
        st.markdown("#### 📡 Sentinel-1 SAR Pass History (C-band VV — Chambal Riverbed)")
        st.caption(
            f"Showing {len(ts_s1)} actual Sentinel-1 SAR acquisitions over the "
            "Chambal monitoring segment, ordered chronologically. "
            "Bright pixels = high radar backscatter (equipment/structures). "
            "Each panel is a real satellite pass — not generated."
        )
        cols = st.columns(len(ts_s1))
        for i, entry in enumerate(ts_s1):
            with cols[i]:
                if entry.get("url"):
                    st.image(entry["url"], use_container_width=True)
                    st.markdown(
                        f'<div class="rw-sat-date" style="font-size:10px">{entry.get("date", "")}</div>',
                        unsafe_allow_html=True,
                    )
    else:
        st.markdown("#### 📡 Sentinel-1 SAR Pass History")
        st.info("No time-series data yet. Run `refresh_anomaly_cache.py`.", icon=None)

# ── Sidebar image guide ───────────────────────────────────────────────────────
with st.sidebar:
    with st.expander("📖 Image Colour Guide", expanded=False):
        st.markdown("""
**True Colour (Sentinel-2)**
Normal RGB — what you'd see from an aircraft on a clear day.

**NDWI (Water/Sandbar Index)**
- 🟤 Brown/wheat = dry, exposed sandbar
- 💛 Light yellow = moist sand
- 🔵 Blue = water channel
- 🌑 Dark = vegetation/land

**SAR (Sentinel-1, C-band)**
- ⬜ Bright = high radar return (metal structures, wet surfaces)
- ⬛ Dark = smooth surface (dry sand, calm water)

**Log-Ratio Change Map**
- 🔴 Red = backscatter *increased* vs. baseline (possible equipment arrival)
- 🔵 Blue = backscatter *decreased* vs. baseline
- ⬜ White = no significant change
        """)
    with st.expander("📡 Pipeline Status", expanded=False):
        firms_key = os.environ.get("FIRMS_API_KEY", "")
        st.markdown(f"**GEE Auth:** ✅ Configured")
        st.markdown(f"**Chambal Imagery:** {'✅ Cached' if imagery_cache else '⏳ Pending'}")
        st.markdown(f"**Baseline Score:** {'✅ Computed' if baseline_score else '⏳ Pending'}")
        st.markdown(f"**FIRMS API Key:** {'✅ Set' if firms_key else '❌ Not set (add to .env)'}")
        if baseline_score:
            st.markdown(f"**Last Run:** {baseline_score.get('computed_at', 'unknown')[:10]}")

# ── Methodology expander ──────────────────────────────────────────────────────
st.markdown('<hr class="rw-divider">', unsafe_allow_html=True)
with st.expander("📐 What does 'Anomaly detected' actually mean?"):
    st.markdown("""
**River Watch does NOT:**
- Measure riverbed depth or volume extracted — SAR does not see through water to the bed
- Confirm illegal mining — anomalies are statistical flags, not legal conclusions
- Provide real-time data — Sentinel-1/2 revisit is ~6 days; see acquisition dates on each image

**River Watch DOES:**
- Flag unusual SAR backscatter consistent with metal equipment on a sandbar relative to a quiet baseline
- Flag sandbar area changes outside this segment's own historical seasonal range (not a global threshold)
- Provide these flags with actual satellite imagery, exact dates, and full hedge language

**Every flag requires human review** — legal, journalistic, or on-ground — before it means anything.
""")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown('<hr class="rw-divider">', unsafe_allow_html=True)
st.caption(
    "River Watch is independent of and not affiliated with any government agency. "
    "All anomaly flags are preliminary and require human investigation to confirm. "
    "Satellite data: ESA Copernicus — open licence."
)
st.markdown(
    '<span style="color:#4a5580;font-size:11px">✦ made by hssn</span>',
    unsafe_allow_html=True,
)
