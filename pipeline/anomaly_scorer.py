"""
anomaly_scorer.py — combines Signal 1 (SAR backscatter) and Signal 2 (NDWI
morphology vs. seasonal baseline) into a single hedged anomaly score per pass.

This module deliberately does NOT produce a binary "illegal mining: yes/no".
It produces a score + a small set of structured flags, and the app layer is
responsible for rendering those with the hedged language required by spec
Section 2.1 ("Anomaly detected — under review", never "confirmed").
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from pipeline.sar_anomaly import SarAnomalyResult
from pipeline.seasonal_baseline_builder import SegmentBaseline, is_within_seasonal_range


class AnomalyLevel(str, Enum):
    NONE = "none"  # nothing notable
    LOW = "low"  # weak/ambiguous signal, worth a footnote, not a flag
    ELEVATED = "elevated"  # one signal fired, or both fired weakly
    UNDER_REVIEW = "under_review"  # both signals fired meaningfully -- the
    # highest level this system ever assigns. Never "confirmed".


@dataclass
class AnomalyScore:
    segment_id: str
    pass_date: str
    level: AnomalyLevel
    label: str  # human-facing hedged label, ready to render
    sar_triggered: bool
    sar_flagged_area_sq_m: Optional[float]
    sar_peak_log_ratio_db: Optional[float]
    morphology_triggered: Optional[bool]  # None if no seasonal baseline available
    morphology_observed_sq_m: Optional[float]
    morphology_baseline_note: str
    confidence_note: str
    last_sar_pass: Optional[str]
    last_optical_pass: Optional[str]


SAR_AREA_TRIGGER_SQ_M = 200.0  # minimum flagged area to count SAR signal as "triggered"
# rather than isolated speckle noise. Starting default -- recalibrate after
# backtesting against case_001 and any future verified cases.


def score_pass(
    segment_id: str,
    pass_date: str,
    sar_result: Optional[SarAnomalyResult],
    baseline: Optional[SegmentBaseline],
    observed_sandbar_sq_m: Optional[float],
    last_sar_pass: Optional[str] = None,
    last_optical_pass: Optional[str] = None,
) -> AnomalyScore:
    """
    Combine the two signals for a single pass/date into one hedged AnomalyScore.

    sar_result: output of sar_anomaly.detect_anomaly() + reduce_stats(), or None
        if no S1 pass was available for this window.
    baseline / observed_sandbar_sq_m: seasonal baseline + this pass's measured
        sandbar area, or None if unavailable (e.g. cloud cover with no S1 backup
        for that exact date).
    """
    sar_triggered = False
    sar_flagged_area = None
    sar_peak_db = None
    if sar_result is not None:
        sar_flagged_area = sar_result.flagged_area_sq_m
        sar_peak_db = sar_result.peak_log_ratio_db
        if sar_flagged_area is not None and sar_flagged_area >= SAR_AREA_TRIGGER_SQ_M:
            sar_triggered = True

    morphology_triggered: Optional[bool] = None
    morphology_note = "No seasonal baseline available for this month yet."
    target_month = datetime.strptime(pass_date, "%Y-%m-%d").month

    if baseline is not None and observed_sandbar_sq_m is not None:
        within_range = is_within_seasonal_range(baseline, target_month, observed_sandbar_sq_m)
        if within_range is None:
            morphology_triggered = None
            morphology_note = (
                f"No baseline samples for month {target_month} yet — "
                "morphology signal not assessable."
            )
        else:
            morphology_triggered = not within_range
            morphology_note = (
                "Outside this segment's historical seasonal range for this month."
                if morphology_triggered
                else "Within this segment's historical seasonal range for this month."
            )

    level, label = _classify(sar_triggered, morphology_triggered)

    confidence_note = (
        "This is an automated anomaly flag, not a confirmation of illegal activity. "
        "Anomalies reflect deviation from expected radar backscatter and/or seasonal "
        "sandbar extent, and require human review (legal, journalistic, or on-ground) "
        "before any conclusion is drawn."
    )

    return AnomalyScore(
        segment_id=segment_id,
        pass_date=pass_date,
        level=level,
        label=label,
        sar_triggered=sar_triggered,
        sar_flagged_area_sq_m=sar_flagged_area,
        sar_peak_log_ratio_db=sar_peak_db,
        morphology_triggered=morphology_triggered,
        morphology_observed_sq_m=observed_sandbar_sq_m,
        morphology_baseline_note=morphology_note,
        confidence_note=confidence_note,
        last_sar_pass=last_sar_pass,
        last_optical_pass=last_optical_pass,
    )


def _classify(
    sar_triggered: bool, morphology_triggered: Optional[bool]
) -> tuple[AnomalyLevel, str]:
    """
    Hedged classification. Note there is deliberately no level that uses the
    words "confirmed", "illegal", or "mining" -- see spec Section 2.1 and 9.
    """
    if sar_triggered and morphology_triggered:
        return (
            AnomalyLevel.UNDER_REVIEW,
            "Anomaly detected on both signals — under review",
        )
    if sar_triggered or morphology_triggered:
        return (
            AnomalyLevel.ELEVATED,
            "Anomaly detected on one signal — under review",
        )
    if sar_triggered is False and morphology_triggered is False:
        return (AnomalyLevel.NONE, "No anomaly detected for this pass")
    return (
        AnomalyLevel.LOW,
        "Insufficient data this pass — anomaly status not assessable",
    )
