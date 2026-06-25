"""
load_css.py — injects the River Watch "Satellite Command" design system
into Streamlit pages. Call load_css() once near the top of every page.

Design tokens:
  Background:      #03071e  (near-black navy)
  Surface:         #0a0e2a  (dark navy card)
  Border:          #1a2040
  Accent-amber:    #ffd60a  (anomaly alert)
  Accent-cyan:     #00b4d8  (data/info)
  Accent-green:    #52b788  (baseline/safe)
  Accent-red:      #e63946  (high severity)
  Text-primary:    #f0f4ff
  Text-secondary:  #8896b3
"""

from __future__ import annotations

import os

import streamlit as st

CSS_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "style.css")

DESIGN_SYSTEM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

* { font-family: 'DM Sans', sans-serif !important; }

.stApp { background: #03071e; }

[data-testid="stSidebar"] {
    background: #0a0e2a !important;
    border-right: 1px solid #1a2040;
}
[data-testid="stSidebar"] .block-container { padding: 1.5rem 1rem; }

/* Cards */
.rw-card {
    background: #0a0e2a;
    border: 1px solid #1a2040;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
}
.rw-card-2 {
    background: #0f1535;
    border: 1px solid #1a2040;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 12px;
}

/* Anomaly badge */
.rw-badge-anomaly {
    display: inline-block;
    background: rgba(255, 214, 10, 0.15);
    color: #ffd60a;
    border: 1px solid rgba(255, 214, 10, 0.3);
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.rw-badge-safe {
    display: inline-block;
    background: rgba(82, 183, 136, 0.15);
    color: #52b788;
    border: 1px solid rgba(82, 183, 136, 0.3);
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.05em;
}
.rw-badge-review {
    display: inline-block;
    background: rgba(247, 127, 0, 0.15);
    color: #f77f00;
    border: 1px solid rgba(247, 127, 0, 0.3);
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.05em;
}
.rw-badge-verified {
    display: inline-block;
    background: rgba(0, 180, 216, 0.15);
    color: #00b4d8;
    border: 1px solid rgba(0, 180, 216, 0.3);
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.05em;
}

/* Satellite image labels */
.rw-sat-label {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px;
    color: #8896b3;
    margin-top: 6px;
    text-align: center;
}
.rw-sat-date {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px;
    color: #ffd60a;
    text-align: center;
    font-weight: 500;
}

/* Data values */
.rw-data-value {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 22px;
    font-weight: 500;
    color: #ffd60a;
    display: block;
}
.rw-data-label {
    font-size: 11px;
    color: #8896b3;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    display: block;
}
.rw-data-flag {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px;
    color: #e63946;
    font-weight: 500;
}

/* Hedge notice */
.rw-hedge-notice {
    background: rgba(0, 180, 216, 0.08);
    border-left: 3px solid #00b4d8;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    font-size: 13px;
    color: #8896b3;
    font-style: italic;
    margin: 16px 0;
}

/* Warning hedge */
.rw-hedge-warning {
    background: rgba(255, 214, 10, 0.06);
    border-left: 3px solid #ffd60a;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    font-size: 13px;
    color: #8896b3;
    margin: 16px 0;
}

/* Section dividers */
.rw-divider {
    border: none;
    border-top: 1px solid #1a2040;
    margin: 24px 0;
}

/* Hero copy */
.rw-hero {
    padding: 32px 0 16px 0;
}
.rw-hero-title {
    font-size: 2.2em;
    font-weight: 700;
    color: #f0f4ff;
    line-height: 1.2;
    margin-bottom: 8px;
}
.rw-hero-sub {
    font-size: 1.1em;
    color: #8896b3;
    margin-bottom: 24px;
    line-height: 1.6;
}

/* Stat strip */
.rw-stat-strip {
    display: flex;
    gap: 32px;
    padding: 20px 24px;
    background: #0a0e2a;
    border: 1px solid #1a2040;
    border-radius: 10px;
    margin: 20px 0;
    flex-wrap: wrap;
}
.rw-stat-item { text-align: center; }

/* Image grid */
.rw-img-container {
    border-radius: 8px;
    border: 1px solid #1a2040;
    overflow: hidden;
    background: #0a0e2a;
    padding: 2px;
}

/* Mono coords */
.rw-mono {
    font-family: 'JetBrains Mono', monospace !important;
    color: #8896b3;
    font-size: 12px;
}

/* How-it-works cards */
.rw-how-card {
    background: #0a0e2a;
    border: 1px solid #1a2040;
    border-radius: 10px;
    padding: 20px;
    height: 100%;
}
.rw-how-number {
    font-size: 1.4em;
    font-weight: 700;
    color: #ffd60a;
    margin-bottom: 8px;
}
.rw-how-title {
    font-size: 1em;
    font-weight: 600;
    color: #f0f4ff;
    margin-bottom: 6px;
}
.rw-how-desc {
    font-size: 0.9em;
    color: #8896b3;
    line-height: 1.5;
}

/* Legal reference */
.rw-legal-ref {
    background: #0a0e2a;
    border: 1px solid #1a2040;
    border-radius: 8px;
    padding: 16px;
    font-size: 13px;
    color: #8896b3;
}
.rw-legal-ref strong { color: #f0f4ff; }

/* Case ID header */
.rw-case-id {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px;
    color: #4a5580;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
"""


def load_css() -> None:
    # Inject the design system CSS
    st.markdown(f"<style>{DESIGN_SYSTEM_CSS}</style>", unsafe_allow_html=True)

    # Also load any custom style.css if it exists
    if os.path.isfile(CSS_PATH):
        with open(CSS_PATH) as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
