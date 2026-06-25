"""
test_anomaly_scorer.py — unit tests for the hedged classification logic in
pipeline/anomaly_scorer.py. These tests do NOT require Earth Engine
credentials -- they exercise the pure-Python scoring/classification logic
with mocked inputs, so they can run in any environment (including CI).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.anomaly_scorer import AnomalyLevel, _classify, score_pass
from pipeline.sar_anomaly import SarAnomalyResult
from pipeline.seasonal_baseline_builder import MonthlyBaseline, SegmentBaseline


def make_baseline(month: int, p10: float, median: float, p90: float) -> SegmentBaseline:
    return SegmentBaseline(
        segment_id="test_segment",
        built_at="2026-01-01T00:00:00Z",
        history_years=5,
        monthly=[MonthlyBaseline(month=month, n_samples=10, p10_sq_m=p10, median_sq_m=median, p90_sq_m=p90)],
    )


class TestClassify:
    def test_both_triggered_is_under_review(self):
        level, label = _classify(sar_triggered=True, morphology_triggered=True)
        assert level == AnomalyLevel.UNDER_REVIEW
        assert "confirmed" not in label.lower()
        assert "illegal" not in label.lower()

    def test_one_triggered_is_elevated(self):
        level, _ = _classify(sar_triggered=True, morphology_triggered=False)
        assert level == AnomalyLevel.ELEVATED

        level2, _ = _classify(sar_triggered=False, morphology_triggered=True)
        assert level2 == AnomalyLevel.ELEVATED

    def test_neither_triggered_is_none(self):
        level, label = _classify(sar_triggered=False, morphology_triggered=False)
        assert level == AnomalyLevel.NONE
        assert "no anomaly" in label.lower()

    def test_missing_morphology_data_is_low_not_none(self):
        # sar_triggered False but morphology_triggered None (no baseline data)
        # must NOT be silently treated as "none" -- that would imply a clean
        # reading that was never actually assessed.
        level, label = _classify(sar_triggered=False, morphology_triggered=None)
        assert level == AnomalyLevel.LOW
        assert "not assessable" in label.lower()

    def test_no_label_ever_claims_confirmation(self):
        for sar in (True, False):
            for morph in (True, False, None):
                _, label = _classify(sar_triggered=sar, morphology_triggered=morph)
                assert "confirmed" not in label.lower()
                assert "illegal" not in label.lower()


class TestScorePass:
    def test_sar_triggered_by_large_flagged_area(self):
        sar_result = SarAnomalyResult(
            segment_id="test_segment",
            pass_date="2023-01-01",
            threshold_db=3.0,
            flagged_pixel_count=500,
            flagged_area_sq_m=5000.0,
            peak_log_ratio_db=8.2,
        )
        baseline = make_baseline(month=1, p10=1000, median=2000, p90=3000)

        score = score_pass(
            segment_id="test_segment",
            pass_date="2023-01-01",
            sar_result=sar_result,
            baseline=baseline,
            observed_sandbar_sq_m=6000.0,  # well above p90 -> morphology triggers too
        )

        assert score.sar_triggered is True
        assert score.morphology_triggered is True
        assert score.level == AnomalyLevel.UNDER_REVIEW
        assert "under review" in score.label.lower()
        assert "not a confirmation" in score.confidence_note.lower()

    def test_within_seasonal_range_does_not_trigger_morphology(self):
        sar_result = SarAnomalyResult(
            segment_id="test_segment",
            pass_date="2023-06-15",
            threshold_db=3.0,
            flagged_area_sq_m=10.0,  # below trigger threshold
            peak_log_ratio_db=1.1,
        )
        baseline = make_baseline(month=6, p10=1000, median=2000, p90=3000)

        score = score_pass(
            segment_id="test_segment",
            pass_date="2023-06-15",
            sar_result=sar_result,
            baseline=baseline,
            observed_sandbar_sq_m=2100.0,  # within range
        )

        assert score.sar_triggered is False
        assert score.morphology_triggered is False
        assert score.level == AnomalyLevel.NONE

    def test_no_baseline_data_does_not_force_false_negative(self):
        sar_result = SarAnomalyResult(
            segment_id="test_segment",
            pass_date="2023-03-01",
            threshold_db=3.0,
            flagged_area_sq_m=5000.0,
            peak_log_ratio_db=7.0,
        )
        score = score_pass(
            segment_id="test_segment",
            pass_date="2023-03-01",
            sar_result=sar_result,
            baseline=None,  # no baseline at all
            observed_sandbar_sq_m=None,
        )
        assert score.sar_triggered is True
        assert score.morphology_triggered is None
        # one signal triggered, the other unassessable -> elevated, not "none"
        assert score.level == AnomalyLevel.ELEVATED


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
