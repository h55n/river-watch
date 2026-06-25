"""
streamlit_app.py — main entrypoint for River Watch.

Run with: streamlit run app/streamlit_app.py

Landing page. Tier 1 (Anomaly Watch) and Tier 2 (Case Files) live
in app/pages/ and appear automatically in Streamlit's multipage sidebar nav.

CRITICAL: This file must NEVER call ee.Initialize() or any GEE API.
All GEE work runs in scripts/refresh_anomaly_cache.py (offline pipeline).
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.components.load_css import load_css

st.set_page_config(
    page_title="River Watch — Satellite Evidence for India's Rivers",
    page_icon="🛰️",
    layout="wide",
)
load_css()

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="rw-hero">
  <div class="rw-hero-title">🛰️ River Watch</div>
  <div class="rw-hero-sub">
    Free, open, evidence-grade satellite monitoring for India's rivers.<br>
    Built to give lawyers, journalists, and communities the <strong>dated proof</strong>
    they need — before the sandbar disappears.
  </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.link_button("→ View Anomaly Watch", url="/anomaly_watch", type="primary", use_container_width=True)
with col2:
    st.link_button("→ Read Case Files", url="/case_files", use_container_width=True)
with col3:
    st.link_button("GitHub ↗", url="https://github.com/", use_container_width=True)

st.markdown('<hr class="rw-divider">', unsafe_allow_html=True)

# ── Stats strip ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="rw-stat-strip">
  <div class="rw-stat-item">
    <span class="rw-data-value">1</span>
    <span class="rw-data-label">Monitored Stretch</span>
  </div>
  <div class="rw-stat-item">
    <span class="rw-data-value">1</span>
    <span class="rw-data-label">Verified Case File</span>
  </div>
  <div class="rw-stat-item">
    <span class="rw-data-value">~6-day</span>
    <span class="rw-data-label">SAR Revisit Cadence</span>
  </div>
  <div class="rw-stat-item">
    <span class="rw-data-value">Free</span>
    <span class="rw-data-label">Open Source (MIT)</span>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="rw-divider">', unsafe_allow_html=True)

# ── How it works ──────────────────────────────────────────────────────────────
st.markdown("### How It Works")
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
<div class="rw-how-card">
  <div class="rw-how-number">1</div>
  <div class="rw-how-title">Sentinel-1 SAR</div>
  <div class="rw-how-desc">
    Equipment and vessel backscatter anomaly detection — even at night, under clouds.
    Log-ratio change between a seasonal quiet-state baseline and the target pass.
    Flagged area = statistically unusual radar return in metal-equipment size range.
  </div>
</div>
""", unsafe_allow_html=True)

with c2:
    st.markdown("""
<div class="rw-how-card">
  <div class="rw-how-number">2</div>
  <div class="rw-how-title">Seasonal Baseline</div>
  <div class="rw-how-desc">
    12-month rolling history, per segment, prevents monsoon false positives —
    the most rigorous method. We never compare a dry-season "before" to a monsoon
    "after" without adjusting for ordinary channel variation.
  </div>
</div>
""", unsafe_allow_html=True)

with c3:
    st.markdown("""
<div class="rw-how-card">
  <div class="rw-how-number">3</div>
  <div class="rw-how-title">Evidence Card</div>
  <div class="rw-how-desc">
    Dated. Citable. Downloadable. Ready for court filings and RTI applications.
    Every card includes the actual satellite imagery, acquisition dates,
    anomaly score, hedge language, and legal source reference.
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="rw-divider">', unsafe_allow_html=True)

# ── What this is / isn't ──────────────────────────────────────────────────────
col_a, col_b = st.columns(2)
with col_a:
    st.markdown("#### ✅ What this is")
    st.markdown("""
- Free Sentinel-1 (SAR radar) + Sentinel-2 (optical) monitoring
- Flags **anomalies** — unusual radar backscatter and sandbar area outside seasonal norms
- Imagery from the **Copernicus programme (ESA)**, used under open licence
- Public, no login required, zero cost
- Transparent statistical method — not a black-box AI
""")
with col_b:
    st.markdown("#### ❌ What this is NOT")
    st.markdown("""
- **Not** riverbed depth/elevation — SAR does not see through water to the bed
- **Not** near-real-time — improving toward ~6-day revisit (Sentinel-1C + 1D); see timestamps on each layer
- **Not** "illegal mining confirmed" — anomalies require human review
- **Not** a deforestation tool — that's [Global Forest Watch](https://globalforestwatch.org)'s job (credited layer)
- **Not** a replacement for state enforcement — supplementary evidence only
""")

st.markdown('<hr class="rw-divider">', unsafe_allow_html=True)

# ── Data sources ──────────────────────────────────────────────────────────────
st.markdown("#### Data Sources & Credits")
s1, s2, s3, s4 = st.columns(4)
with s1:
    st.markdown("**ESA Copernicus**\nSentinel-1 SAR (C-band, GRD)\nSentinel-2 Optical (10m)")
with s2:
    st.markdown("**Google Earth Engine**\nProcessing pipeline\nFree tier — no paid compute")
with s3:
    st.markdown("**NASA FIRMS**\nThermal anomaly reference layer\n(fires/kilns — not mining)")
with s4:
    st.markdown("**Global Forest Watch (WRI)**\nForest alert reference layer\n(credited, not our detection)")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown('<hr class="rw-divider">', unsafe_allow_html=True)
st.caption(
    "River Watch is independent of and not affiliated with any government agency. "
    "All anomaly flags are preliminary and require human investigation to confirm. "
    "MIT Licence · Open source · "
    "Satellite data: ESA Copernicus — open licence."
)
st.markdown(
    '<span style="color:#4a5580;font-size:11px">✦ made by hssn</span>',
    unsafe_allow_html=True,
)
