"""
test_seasonal_baseline_builder.py — unit tests for the pure-Python parts of
the seasonal baseline builder (percentile math, save/load round-trip, and
is_within_seasonal_range's None-handling). No Earth Engine calls.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.seasonal_baseline_builder import (
    MonthlyBaseline,
    SegmentBaseline,
    _percentile,
    is_within_seasonal_range,
    load_baseline,
    save_baseline,
)


class TestPercentile:
    def test_median_of_sorted_list(self):
        assert _percentile([1, 2, 3, 4, 5], 50) == 3

    def test_p10_and_p90_bounds(self):
        vals = list(range(1, 11))  # 1..10
        assert _percentile(vals, 0) == 1
        assert _percentile(vals, 100) == 10

    def test_empty_list_returns_zero(self):
        assert _percentile([], 50) == 0.0


class TestSegmentBaselineRoundTrip:
    def test_save_and_load(self, tmp_path, monkeypatch):
        import pipeline.seasonal_baseline_builder as sbb

        monkeypatch.setattr(sbb, "BASELINE_DIR", str(tmp_path))

        baseline = SegmentBaseline(
            segment_id="roundtrip_test",
            built_at="2026-01-01T00:00:00Z",
            history_years=5,
            monthly=[
                MonthlyBaseline(month=1, n_samples=12, p10_sq_m=1000, median_sq_m=2000, p90_sq_m=3000),
                MonthlyBaseline(month=7, n_samples=8, p10_sq_m=500, median_sq_m=900, p90_sq_m=1500),
            ],
        )
        path = save_baseline(baseline)
        assert os.path.exists(path)

        loaded = load_baseline("roundtrip_test")
        assert loaded is not None
        assert loaded.segment_id == "roundtrip_test"
        assert loaded.get_month(1).median_sq_m == 2000
        assert loaded.get_month(7).p90_sq_m == 1500
        assert loaded.get_month(12) is None  # not present, must return None not raise

    def test_load_missing_segment_returns_none(self, tmp_path, monkeypatch):
        import pipeline.seasonal_baseline_builder as sbb

        monkeypatch.setattr(sbb, "BASELINE_DIR", str(tmp_path))
        assert load_baseline("does_not_exist") is None


class TestIsWithinSeasonalRange:
    def setup_method(self):
        self.baseline = SegmentBaseline(
            segment_id="x",
            built_at="2026-01-01T00:00:00Z",
            history_years=5,
            monthly=[MonthlyBaseline(month=6, n_samples=10, p10_sq_m=1000, median_sq_m=2000, p90_sq_m=3000)],
        )

    def test_within_range(self):
        assert is_within_seasonal_range(self.baseline, 6, 2500) is True

    def test_outside_range_above(self):
        assert is_within_seasonal_range(self.baseline, 6, 5000) is False

    def test_outside_range_below(self):
        assert is_within_seasonal_range(self.baseline, 6, 100) is False

    def test_missing_month_returns_none_not_false(self):
        # Critical: a month with no baseline data must return None (cannot
        # assess), never False (which would silently read as "in range").
        result = is_within_seasonal_range(self.baseline, 11, 9999)
        assert result is None


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
