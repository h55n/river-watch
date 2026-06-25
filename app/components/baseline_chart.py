"""
baseline_chart.py — renders the "seasonal baseline vs. current reading" chart
that answers the most likely reviewer question ("is this just monsoon
variation?") before it's asked. Used in both the Anomaly Watch map popups and
Evidence Cards (spec Section 5.1, 5.3).
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.graph_objects as go

from pipeline.seasonal_baseline_builder import SegmentBaseline

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def render_baseline_chart(
    baseline: Optional[SegmentBaseline],
    observed_month: Optional[int] = None,
    observed_value_sq_m: Optional[float] = None,
) -> go.Figure:
    """
    Build a Plotly figure showing the p10-p90 seasonal range per month (a
    shaded band) plus the median line, with the current observed reading
    overlaid as a marker if provided.

    If baseline is None (not yet built for this segment), returns a figure
    with an explicit "no baseline yet" annotation rather than a misleading
    empty chart.
    """
    fig = go.Figure()

    if baseline is None or not baseline.monthly:
        fig.add_annotation(
            text="No seasonal baseline built yet for this segment.<br>"
                 "Morphology anomaly status cannot be assessed until "
                 "seasonal_baseline_builder.py has run.",
            showarrow=False,
            font=dict(size=13),
        )
        fig.update_layout(
            xaxis=dict(visible=False), yaxis=dict(visible=False), height=300
        )
        return fig

    df = pd.DataFrame(
        [
            {
                "month": m.month,
                "month_name": MONTH_NAMES[m.month - 1],
                "p10": m.p10_sq_m,
                "median": m.median_sq_m,
                "p90": m.p90_sq_m,
                "n_samples": m.n_samples,
            }
            for m in sorted(baseline.monthly, key=lambda x: x.month)
        ]
    )

    fig.add_trace(
        go.Scatter(
            x=df["month_name"], y=df["p90"], mode="lines",
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["month_name"], y=df["p10"], mode="lines",
            fill="tonexty", fillcolor="rgba(58,125,68,0.18)",
            line=dict(width=0), name="Historical p10-p90 range",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["month_name"], y=df["median"], mode="lines+markers",
            line=dict(color="#3a7d44", width=2), name="Historical median",
        )
    )

    if observed_month is not None and observed_value_sq_m is not None:
        fig.add_trace(
            go.Scatter(
                x=[MONTH_NAMES[observed_month - 1]],
                y=[observed_value_sq_m],
                mode="markers",
                marker=dict(size=14, color="#c1440e", symbol="diamond"),
                name="Current reading",
            )
        )

    fig.update_layout(
        title="Exposed sandbar area vs. this segment's seasonal baseline",
        yaxis_title="Area (sq. m)",
        xaxis_title="Month",
        height=380,
        margin=dict(t=50, b=40, l=40, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig
