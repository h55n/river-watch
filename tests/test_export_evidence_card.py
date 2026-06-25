"""
test_export_evidence_card.py — unit tests for Evidence Card construction and
serialization. No Earth Engine calls.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.anomaly_scorer import AnomalyLevel, score_pass
from pipeline.export_evidence_card import HEDGE_LANGUAGE, build_evidence_card, save_evidence_card
from pipeline.sar_anomaly import SarAnomalyResult
from pipeline.seasonal_baseline_builder import MonthlyBaseline, SegmentBaseline


def _make_score():
    sar = SarAnomalyResult(
        segment_id="chambal_dholpur_morena",
        pass_date="2023-01-01",
        threshold_db=3.0,
        flagged_area_sq_m=5000.0,
        peak_log_ratio_db=8.2,
    )
    baseline = SegmentBaseline(
        segment_id="chambal_dholpur_morena",
        built_at="2026-01-01T00:00:00Z",
        history_years=5,
        monthly=[MonthlyBaseline(month=1, n_samples=8, p10_sq_m=1000, median_sq_m=2000, p90_sq_m=3000)],
    )
    return score_pass(
        segment_id="chambal_dholpur_morena",
        pass_date="2023-01-01",
        sar_result=sar,
        baseline=baseline,
        observed_sandbar_sq_m=6000.0,
        last_sar_pass="2023-01-01",
        last_optical_pass="2023-01-03",
    )


class TestBuildEvidenceCard:
    def test_card_always_carries_hedge_language(self):
        card = build_evidence_card("case_test", _make_score())
        assert card.hedge_language == HEDGE_LANGUAGE
        assert "not a confirmed finding" in card.hedge_language.lower()

    def test_card_fields_populated_from_score(self):
        score = _make_score()
        card = build_evidence_card("case_test", score, source_citation="NGT order 2023-02-06")
        assert card.anomaly_level == AnomalyLevel.UNDER_REVIEW.value
        assert card.sar_flagged_area_sq_m == 5000.0
        assert card.morphology_observed_sq_m == 6000.0
        assert card.source_citation == "NGT order 2023-02-06"

    def test_to_json_round_trips(self):
        card = build_evidence_card("case_test", _make_score())
        parsed = json.loads(card.to_json())
        assert parsed["card_id"] == "case_test"
        assert parsed["segment_id"] == "chambal_dholpur_morena"


class TestSaveEvidenceCard:
    def test_save_creates_file(self, tmp_path):
        card = build_evidence_card("case_test", _make_score())
        path = save_evidence_card(card, case_dir=str(tmp_path))
        assert os.path.exists(path)
        with open(path) as f:
            data = json.load(f)
        assert data["card_id"] == "case_test"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
