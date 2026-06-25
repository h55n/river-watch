"""
evidence_card.py — Streamlit rendering of the Evidence Card (spec Section 5.3).

This component renders an Evidence Card from the imagery cache + anomaly score.
Export is JSON only (client-side, no external service).

IMPORTANT: Never show imagery without a visible acquisition date.
Never use the word "confirmed" or "illegal" in any label.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

import streamlit as st


HEDGE_LANGUAGE = (
    "This Evidence Card presents satellite anomaly data temporally consistent "
    "with the referenced NGT case. It does not independently confirm illegal "
    "activity and must be used alongside, not as a replacement for, primary "
    "legal documentation. Anomaly detection is automated; human investigation "
    "is required to confirm."
)


def render_evidence_card_v2(
    imagery_cache: Optional[dict],
    anomaly_score: Optional[dict],
    case_meta: Optional[dict] = None,
) -> None:
    """
    Render an Evidence Card panel from cached imagery + anomaly score dicts.

    imagery_cache: contents of data/imagery_cache/chambal_001_imagery.json
    anomaly_score: contents of data/baselines/baseline_chambal_001.json
    case_meta: contents of data/case_files/case_001/metadata.json (optional)
    """
    # Extract values safely
    sar_delta = anomaly_score.get("sar_logratio_delta") if anomaly_score else None
    ndwi_change = anomaly_score.get("ndwi_area_change_pct") if anomaly_score else None
    combined_score = anomaly_score.get("combined_score") if anomaly_score else None
    confidence = anomaly_score.get("confidence", "—") if anomaly_score else "—"
    sar_flag = anomaly_score.get("sar_anomaly_flag", False) if anomaly_score else False
    ndwi_flag = anomaly_score.get("ndwi_anomaly_flag", False) if anomaly_score else False
    computed_at = anomaly_score.get("computed_at", "—") if anomaly_score else "—"

    st.markdown(
        f'<span class="rw-mono">Score computed: {computed_at}</span>',
        unsafe_allow_html=True,
    )

    # Anomaly status badge
    if sar_flag or ndwi_flag:
        st.markdown(
            '<span class="rw-badge-anomaly">⚠️ Anomaly Detected — Under Review</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="rw-badge-safe">Within Baseline Range</span>',
            unsafe_allow_html=True,
        )

    # Metrics row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        delta_str = f"{sar_delta:+.1f} dB" if sar_delta is not None else "—"
        st.markdown(
            f'<span class="rw-data-value">{delta_str}</span>'
            f'<span class="rw-data-label">SAR Δ Backscatter</span>'
            + (f'<span class="rw-data-flag">▲ FLAGGED</span>' if sar_flag else ""),
            unsafe_allow_html=True,
        )
    with c2:
        ndwi_str = f"{ndwi_change:+.1f}%" if ndwi_change is not None else "—"
        st.markdown(
            f'<span class="rw-data-value">{ndwi_str}</span>'
            f'<span class="rw-data-label">NDWI Sandbar Change</span>'
            + (f'<span class="rw-data-flag">▲ FLAGGED</span>' if ndwi_flag else ""),
            unsafe_allow_html=True,
        )
    with c3:
        score_str = f"{combined_score:.2f} / 1.0" if combined_score is not None else "—"
        st.markdown(
            f'<span class="rw-data-value">{score_str}</span>'
            f'<span class="rw-data-label">Combined Score</span>',
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f'<span class="rw-data-value" style="text-transform:capitalize">{confidence}</span>'
            f'<span class="rw-data-label">Confidence</span>',
            unsafe_allow_html=True,
        )

    # 6-panel image grid
    if imagery_cache:
        st.markdown("#### Satellite Evidence")
        _render_image_grid(imagery_cache)
    else:
        st.info("📡 Imagery not yet cached. Run `refresh_anomaly_cache.py`.", icon=None)

    # Hedge notice
    st.markdown(f"""
<div class="rw-hedge-notice">
  ⚖️ <em>{HEDGE_LANGUAGE}</em>
</div>
""", unsafe_allow_html=True)

    # JSON download
    card_json = _build_evidence_card_json(imagery_cache, anomaly_score, case_meta)
    st.download_button(
        label="⬇️ Download Evidence Card (JSON)",
        data=json.dumps(card_json, indent=2),
        file_name="chambal_001_evidence_card.json",
        mime="application/json",
    )


def _render_image_grid(imagery_cache: dict) -> None:
    """Render the 6-panel before/after evidence image grid."""
    def show_img(col, key: str, label: str):
        entry = imagery_cache.get(key, {})
        url = entry.get("url") if isinstance(entry, dict) else None
        date = entry.get("date") or entry.get("period", "")
        with col:
            if url:
                st.image(url, use_container_width=True)
                st.markdown(
                    f'<div class="rw-sat-label">{label}</div>'
                    f'<div class="rw-sat-date">{date}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="background:#0f1535;border:1px dashed #1a2040;border-radius:8px;'
                    f'padding:24px;text-align:center;color:#4a5580;font-size:12px">'
                    f"🛰️<br>{label}<br>Pending cache"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    c1, c2, c3 = st.columns(3)
    show_img(c1, "before_truecolor", "Before — S2 True Colour")
    show_img(c2, "after_truecolor", "After — S2 True Colour")
    show_img(c3, "logratio", "SAR Log-Ratio Change")

    c4, c5, c6 = st.columns(3)
    show_img(c4, "before_ndwi", "Before — NDWI")
    show_img(c5, "after_ndwi", "After — NDWI")
    show_img(c6, "after_sar", "After — Sentinel-1 SAR")

    st.caption(
        "All imagery: Copernicus Sentinel data (ESA) — open licence. "
        "Processed via Google Earth Engine."
    )


def _build_evidence_card_json(
    imagery_cache: Optional[dict],
    anomaly_score: Optional[dict],
    case_meta: Optional[dict],
) -> dict:
    """Build the full Evidence Card JSON schema."""
    ic = imagery_cache or {}
    sc = anomaly_score or {}

    return {
        "river_watch_evidence_card": True,
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat() + "Z",
        "segment_id": "chambal_001",
        "segment_name": "Chambal River \u2014 Dholpur/Morena",
        "coordinates_center": [26.7, 77.9],
        "anomaly_status": "Anomaly detected \u2014 under review",
        "sar_delta_db": sc.get("sar_logratio_delta"),
        "ndwi_change_pct": sc.get("ndwi_area_change_pct"),
        "combined_score": sc.get("combined_score"),
        "confidence": sc.get("confidence", "pending_gee_run"),
        "sar_anomaly_flag": sc.get("sar_anomaly_flag"),
        "ndwi_anomaly_flag": sc.get("ndwi_anomaly_flag"),
        "baseline_period": sc.get("baseline_period", "2022-06-01 to 2022-12-15"),
        "analysis_period": sc.get("analysis_period", "2022-12-20 to 2023-01-20"),
        "data_quality_notes": sc.get("data_quality_notes"),
        "imagery": {
            "before_truecolor_url": ic.get("before_truecolor", {}).get("url"),
            "before_truecolor_date": ic.get("before_truecolor", {}).get("date"),
            "after_truecolor_url": ic.get("after_truecolor", {}).get("url"),
            "after_truecolor_date": ic.get("after_truecolor", {}).get("date"),
            "before_ndwi_url": ic.get("before_ndwi", {}).get("url"),
            "after_ndwi_url": ic.get("after_ndwi", {}).get("url"),
            "before_sar_url": ic.get("before_sar", {}).get("url"),
            "after_sar_url": ic.get("after_sar", {}).get("url"),
            "sar_logratio_url": ic.get("logratio", {}).get("url"),
            "imagery_cache_generated_at": ic.get("generated_at"),
            "imagery_source": (
                "ESA Copernicus Sentinel-1/Sentinel-2, processed via Google Earth Engine"
            ),
        },
        "legal_reference": {
            "court": "National Green Tribunal",
            "order_date": "2023-02-06",
            "site_visit_date": "2023-01-01",
            "documented_activity": "40-50 tractors hauling sand observed in NGT report",
            "source_url": (
                "http://admin.indiaenvironmentportal.org.in/content/"
                "order-national-green-tribunal-regarding-illegal-sand-mining-"
                "madhya-pradesh-uttar-pradesh-and"
            ),
        },
        "hedge_notice": HEDGE_LANGUAGE,
        "data_licence": (
            "Copernicus Sentinel data (ESA) \u2014 open licence. "
            "Processed via Google Earth Engine free tier."
        ),
    }


# Legacy support — keep old render_evidence_card working for tests
# that may reference it. The new function is render_evidence_card_v2.
from pipeline.export_evidence_card import EvidenceCard  # noqa: E402


def render_evidence_card(card: EvidenceCard) -> None:
    """Legacy evidence card renderer (preserved for backward compatibility)."""
    level_emoji = {
        "none": "🟢",
        "low": "⚪",
        "elevated": "🟠",
        "under_review": "🔶",
    }.get(card.anomaly_level, "⚪")

    with st.container(border=True):
        st.markdown(f"### {level_emoji} {card.anomaly_label}")
        st.caption(f"Segment: `{card.segment_id}` · Pass date: {card.pass_date}")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**SAR signal (equipment/vessel backscatter)**")
            if card.sar_flagged_area_sq_m is not None:
                st.write(f"Flagged area: {card.sar_flagged_area_sq_m:,.0f} sq. m")
            if card.sar_peak_log_ratio_db is not None:
                st.write(f"Peak log-ratio: {card.sar_peak_log_ratio_db:.1f} dB")
            st.caption(f"Last SAR pass: {card.last_sar_pass or 'unknown'}")
        with col2:
            st.markdown("**Morphology signal (sandbar vs. seasonal baseline)**")
            if card.morphology_observed_sq_m is not None:
                st.write(f"Observed exposed area: {card.morphology_observed_sq_m:,.0f} sq. m")
            st.write(card.morphology_baseline_note)
            st.caption(f"Last optical pass: {card.last_optical_pass or 'unknown'}")

        if card.before_image_ref and card.after_image_ref:
            img_col1, img_col2 = st.columns(2)
            with img_col1:
                st.image(card.before_image_ref, caption="Before")
            with img_col2:
                st.image(card.after_image_ref, caption="After")

        st.info(card.hedge_language, icon="⚠️")

        if card.source_citation:
            st.caption(f"Source: {card.source_citation}")

        st.download_button(
            label="Download Evidence Card (JSON)",
            data=card.to_json(),
            file_name=f"{card.card_id}_evidence_card.json",
            mime="application/json",
        )
