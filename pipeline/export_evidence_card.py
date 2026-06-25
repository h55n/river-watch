"""
export_evidence_card.py — builds the atomic "Evidence Card" unit (spec Section 5.3)
used in both Tier 1 (Anomaly Watch) and Tier 2 (Case Files).

An Evidence Card is a structured, downloadable record:
  - coordinates + map thumbnail
  - date(s) of imagery
  - before/after visual
  - anomaly type + score
  - seasonal baseline comparison chart
  - explicit hedge language
  - exportable as JSON (always) and PDF/image (client-side, see app layer)

This module produces the JSON representation. PDF/image export is done
client-side in the Streamlit app (browser-native, no backend) per the
zero-cost tech stack -- see app/components/evidence_card.py.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Optional

from pipeline.anomaly_scorer import AnomalyScore

EVIDENCE_CARD_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "case_files")

HEDGE_LANGUAGE = (
    "This card documents a satellite-derived anomaly, not a confirmed finding. "
    "Anomalies require independent human verification before being treated as "
    "evidence of illegal activity."
)


@dataclass
class EvidenceCard:
    card_id: str
    segment_id: str
    pass_date: str
    generated_at: str
    centroid_lat: Optional[float]
    centroid_lon: Optional[float]
    anomaly_level: str
    anomaly_label: str
    sar_flagged_area_sq_m: Optional[float]
    sar_peak_log_ratio_db: Optional[float]
    morphology_observed_sq_m: Optional[float]
    morphology_baseline_note: str
    last_sar_pass: Optional[str]
    last_optical_pass: Optional[str]
    before_image_ref: Optional[str]
    after_image_ref: Optional[str]
    source_citation: Optional[str]
    hedge_language: str = HEDGE_LANGUAGE

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


def build_evidence_card(
    card_id: str,
    score: AnomalyScore,
    centroid_lat: Optional[float] = None,
    centroid_lon: Optional[float] = None,
    before_image_ref: Optional[str] = None,
    after_image_ref: Optional[str] = None,
    source_citation: Optional[str] = None,
) -> EvidenceCard:
    return EvidenceCard(
        card_id=card_id,
        segment_id=score.segment_id,
        pass_date=score.pass_date,
        generated_at=datetime.now(timezone.utc).isoformat(),
        centroid_lat=centroid_lat,
        centroid_lon=centroid_lon,
        anomaly_level=score.level.value,
        anomaly_label=score.label,
        sar_flagged_area_sq_m=score.sar_flagged_area_sq_m,
        sar_peak_log_ratio_db=score.sar_peak_log_ratio_db,
        morphology_observed_sq_m=score.morphology_observed_sq_m,
        morphology_baseline_note=score.morphology_baseline_note,
        last_sar_pass=score.last_sar_pass,
        last_optical_pass=score.last_optical_pass,
        before_image_ref=before_image_ref,
        after_image_ref=after_image_ref,
        source_citation=source_citation,
    )


def save_evidence_card(card: EvidenceCard, case_dir: Optional[str] = None) -> str:
    """
    Save the Evidence Card JSON under data/case_files/<card_id>/evidence_card.json
    (or a caller-supplied directory, e.g. for the seed case_001 example).
    """
    target_dir = case_dir or os.path.join(EVIDENCE_CARD_DIR, card.card_id)
    os.makedirs(target_dir, exist_ok=True)
    path = os.path.join(target_dir, "evidence_card.json")
    with open(path, "w") as f:
        f.write(card.to_json())
    return path
