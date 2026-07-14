"""
Charts Component
Creates premium Plotly chart figures with a dark theme for
the AirSense IoT Air Quality Monitoring dashboard.
"""
import plotly.graph_objects as go
import numpy as np
from typing import List, Optional


# ═══════════════════════════════════════════════════════════════════════════
# PREMIUM DARK THEME CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

DARK_BG = "#0e1117"
PAPER_BG = "#0e1117"
GRID_COLOR = "rgba(255, 255, 255, 0.06)"
TEXT_COLOR = "#e5e7eb"
MUTED_TEXT = "#6b7280"
FONT_FAMILY = "Inter, system-ui, -apple-system, sans-serif"

# Color palette — blue-cyan-green gradient
LINE_COLORS = ["#06b6d4", "#3b82f6", "#22c55e", "#a855f7", "#f59e0b"]

# ISPU gauge color stops (lo, hi, hex)
ISPU_GAUGE_COLORS = [
    (0,   50,  "#22c55e"),   # Good — green
    (51,  100, "#3b82f6"),   # Moderate — blue
    (101, 200, "#f59e0b"),   # Unhealthy — amber
    (201, 300, "#ef4444"),   # Very Unhealthy — red
    (301, 500, "#1e1b4b"),   # Hazardous — dark indigo
]


# ═══════════════════════════════════════════════════════════════════════════
# SHARED LAYOUT HELPER
# ═══════════════════════════════════════════════════════════════════════════

def _apply_premium_layout(
    fig: go.Figure,
    title: str = "",
    y_label: str = "",
    x_label: str = "",
) -> None:
    """Apply the premium dark-theme layout to a Plotly figure (in-place)."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=DARK_BG,
        title=dict(
            text=title,
            font=dict(size=18, color=TEXT_COLOR, family=FONT_FAMILY),
            x=0.0,
            y=0.98,
        ),
        font=dict(family=FONT_FAMILY, color=TEXT_COLOR, size=12),
        xaxis=dict(
            gridcolor=GRID_COLOR,
            showgrid=True,
            zeroline=False,
            title=dict(text=x_label, font=dict(color=MUTED_TEXT)),
        ),
        yaxis=dict(
            gridcolor=GRID_COLOR,
            showgrid=True,
            zeroline=False,
            title=dict(text=y_label, font=dict(color=MUTED_TEXT)),
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(255,255,255,0.1)",
            borderwidth=1,
            font=dict(color=TEXT_COLOR, size=11),
        ),
        margin=dict(l=60, r=30, t=50, b=50),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#1f2937",
            bordercolor="rgba(255,255,255,0.1)",
            font=dict(color=TEXT_COLOR, family=FONT_FAMILY, size=13),
        ),
    )


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert hex color (e.g. '#06b6d4') to rgba format (e.g. 'rgba(6,182,212,0.12)')."""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


# ═══════════════════════════════════════════════════════════════════════════
# LINE CHART
# ═══════════════════════════════════════════════════════════════════════════

def create_line_chart(
    df,
    x_col: str,
    y_cols: list,
    title: str,
    y_label: str = "",
) -> go.Figure:
    """
    Create a multi-line chart with smooth spline curves and gradient fills.

    Args:
        df: pandas DataFrame containing the data.
        x_col: Column name for the x-axis (typically timestamps).
        y_cols: List of column names to plot as separate lines.
        title: Chart title string.
        y_label: Label for the y-axis.

    Returns:
        A styled Plotly Figure object.
    """
    fig = go.Figure()

    for i, y_col in enumerate(y_cols):
        color = LINE_COLORS[i % len(LINE_COLORS)]
        display_name = y_col.replace("_", " ").title()

        fig.add_trace(
            go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode="lines",
                name=display_name,
                line=dict(
                    color=color,
                    width=2.5,
                    shape="spline",
                    smoothing=1.0,
                ),
                fill="tozeroy" if i == 0 else "tonexty",
                fillcolor=_hex_to_rgba(color, 0.07),
                connectgaps=True,   # bridge over missing data gaps (upload failures)
                hovertemplate=(
                    f"<b>{display_name}</b>: %{{y:.1f}}<extra></extra>"
                ),
            )
        )

    _apply_premium_layout(fig, title, y_label)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# GAUGE CHART
# ═══════════════════════════════════════════════════════════════════════════

def create_gauge_chart(
    value: float,
    title: str,
    min_val: float = 0,
    max_val: float = 500,
    thresholds: Optional[list] = None,
) -> go.Figure:
    """
    Create a gauge / indicator chart for ISPU or single-metric display.

    Args:
        value: Current metric value.
        title: Chart title.
        min_val: Gauge minimum (default 0).
        max_val: Gauge maximum (default 500).
        thresholds: Optional list of (lo, hi, color) tuples.
                    Defaults to ISPU_GAUGE_COLORS.

    Returns:
        A styled Plotly Figure object.
    """
    if thresholds is None:
        thresholds = ISPU_GAUGE_COLORS

    # Build gauge steps
    steps = [
        dict(range=[lo, hi], color=_hex_to_rgba(color, 0.25))
        for lo, hi, color in thresholds
    ]

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title=dict(
                text=title,
                font=dict(size=16, color=TEXT_COLOR, family=FONT_FAMILY),
            ),
            number=dict(
                font=dict(size=48, color="#ffffff", family=FONT_FAMILY),
            ),
            gauge=dict(
                axis=dict(
                    range=[min_val, max_val],
                    tickcolor=MUTED_TEXT,
                    tickfont=dict(color=MUTED_TEXT, size=10),
                ),
                bar=dict(color="#06b6d4", thickness=0.3),
                bgcolor=DARK_BG,
                borderwidth=0,
                steps=steps,
                threshold=dict(
                    line=dict(color="#ffffff", width=3),
                    thickness=0.8,
                    value=value,
                ),
            ),
        )
    )

    fig.update_layout(
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=DARK_BG,
        font=dict(family=FONT_FAMILY, color=TEXT_COLOR, size=12),
        margin=dict(l=30, r=30, t=60, b=20),
        height=280,
    )

    return fig


# ═══════════════════════════════════════════════════════════════════════════
# BAR CHART
# ═══════════════════════════════════════════════════════════════════════════

def create_bar_chart(
    df,
    x_col: str,
    y_col: str,
    title: str,
    color_col: Optional[str] = None,
) -> go.Figure:
    """
    Create a styled bar chart with optional per-bar coloring.

    Args:
        df: pandas DataFrame.
        x_col: Column for x-axis categories.
        y_col: Column for bar heights.
        title: Chart title.
        color_col: Optional column name whose values supply per-bar colours.

    Returns:
        A styled Plotly Figure object.
    """
    # Determine bar colors
    if color_col and color_col in df.columns:
        colors = df[color_col].tolist()
    else:
        # Generate a gradient from cyan → blue
        n = len(df)
        if n <= 1:
            colors = ["#06b6d4"]
        else:
            colors = [
                _interpolate_hex("#06b6d4", "#3b82f6", i / (n - 1))
                for i in range(n)
            ]

    fig = go.Figure(
        go.Bar(
            x=df[x_col],
            y=df[y_col],
            marker=dict(
                color=colors,
                line=dict(width=0),
                opacity=0.85,
            ),
            hovertemplate=(
                f"<b>%{{x}}</b><br>{y_col.replace('_', ' ').title()}"
                f": %{{y:.1f}}<extra></extra>"
            ),
        )
    )

    _apply_premium_layout(fig, title, y_col.replace("_", " ").title())
    fig.update_layout(bargap=0.15)
    return fig


def _interpolate_hex(c1: str, c2: str, t: float) -> str:
    """Linearly interpolate between two hex colours at fraction *t*."""
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


# ═══════════════════════════════════════════════════════════════════════════
# FORECAST CHART
# ═══════════════════════════════════════════════════════════════════════════

def create_forecast_chart(
    timestamps,
    actual_values,
    predicted_values,
    title: str,
) -> go.Figure:
    """
    Create a forecast chart with actual (solid) and predicted (dashed) lines
    plus a shaded confidence-interval band.

    Args:
        timestamps: Sequence of datetime values covering both actual & predicted.
        actual_values: Measured values (may contain None / NaN for future points).
        predicted_values: Predicted values (may contain None / NaN for past points).
        title: Chart title.

    Returns:
        A styled Plotly Figure object.
    """
    fig = go.Figure()

    # Convert to numpy for safe arithmetic
    pred_arr = np.array(predicted_values, dtype=float)

    # Confidence bounds (±15 %)
    upper = pred_arr * 1.15
    lower = np.clip(pred_arr * 0.85, 0, None)

    # ── Upper bound (invisible line) ────────────────────────────────
    fig.add_trace(
        go.Scatter(
            x=list(timestamps),
            y=upper.tolist(),
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # ── Lower bound with fill to upper ──────────────────────────────
    fig.add_trace(
        go.Scatter(
            x=list(timestamps),
            y=lower.tolist(),
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(168, 85, 247, 0.08)",
            name="Confidence Interval",
            showlegend=True,
            hoverinfo="skip",
        )
    )

    # ── Actual data line ────────────────────────────────────────────
    fig.add_trace(
        go.Scatter(
            x=list(timestamps),
            y=list(actual_values),
            mode="lines",
            name="Aktual",
            line=dict(color="#06b6d4", width=2.5, shape="spline", smoothing=1.0),
            hovertemplate="<b>Aktual</b>: %{y:.1f}<extra></extra>",
        )
    )

    # ── Predicted data line (dashed) ────────────────────────────────
    fig.add_trace(
        go.Scatter(
            x=list(timestamps),
            y=list(predicted_values),
            mode="lines",
            name="Prediksi",
            line=dict(color="#a855f7", width=2.5, dash="dash", shape="spline", smoothing=1.0),
            hovertemplate="<b>Prediksi</b>: %{y:.1f}<extra></extra>",
        )
    )

    # ── Vertical boundary annotation ────────────────────────────────
    # Find the last non-null actual value index as the boundary
    try:
        actual_arr = np.array(actual_values, dtype=float)
        valid_mask = ~np.isnan(actual_arr)
        if valid_mask.any():
            boundary_idx = int(np.max(np.where(valid_mask)))
            boundary_ts = timestamps[boundary_idx]
            fig.add_vline(
                x=boundary_ts,
                line=dict(color="rgba(255,255,255,0.2)", width=1.5, dash="dot"),
                annotation_text="Forecast →",
                annotation_font=dict(color=MUTED_TEXT, size=11, family=FONT_FAMILY),
                annotation_position="top right",
            )
    except (ValueError, TypeError, IndexError):
        pass

    _apply_premium_layout(fig, title, "Value")
    return fig
