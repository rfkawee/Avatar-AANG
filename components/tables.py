"""
Tables Component
Renders premium dark-themed HTML tables for sensor data and alerts
in the AirSense IoT Air Quality Monitoring dashboard.
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Optional


# ═══════════════════════════════════════════════════════════════════════════
# DATA TABLE
# ═══════════════════════════════════════════════════════════════════════════

def render_data_table(df: pd.DataFrame, title: Optional[str] = None) -> None:
    """
    Render a pandas DataFrame as a premium styled HTML table.

    Args:
        df: The DataFrame to display.
        title: Optional title rendered above the table.
    """
    # ── Empty state ─────────────────────────────────────────────────
    if df is None or df.empty:
        empty_html = """
        <div style="
            background: rgba(17, 25, 40, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        ">
            <div style="font-size: 36px; margin-bottom: 12px;">📭</div>
            <p style="color: #6b7280; font-size: 14px; margin: 0;">
                No data available
            </p>
        </div>
        """
        st.markdown(empty_html, unsafe_allow_html=True)
        return

    # ── Title ───────────────────────────────────────────────────────
    title_html = ""
    if title:
        title_html = f"""
        <h3 style="
            color: #e5e7eb;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 16px;
            letter-spacing: -0.3px;
        ">{title}</h3>
        """

    # ── Build table HTML ────────────────────────────────────────────
    header_cells = "".join(
        f'<th style="'
        f"padding: 14px 18px;"
        f"text-align: left;"
        f"font-size: 11px;"
        f"font-weight: 600;"
        f"text-transform: uppercase;"
        f"letter-spacing: 0.05em;"
        f"color: #94a3b8;"
        f"white-space: nowrap;"
        f'">{col}</th>'
        for col in df.columns
    )

    body_rows = ""
    for row_idx, (_, row) in enumerate(df.iterrows()):
        bg = (
            "rgba(17, 25, 40, 0.5)"
            if row_idx % 2 == 0
            else "rgba(17, 25, 40, 0.25)"
        )
        cells = ""
        for col_idx, val in enumerate(row):
            # Format floats
            if isinstance(val, float):
                display = f"{val:.1f}"
            else:
                display = str(val) if val is not None else "-"

            # First column styling
            if col_idx == 0:
                cell_style = "color: #f3f4f6; font-weight: 500;"
            else:
                cell_style = "color: #d1d5db;"

            cells += (
                f'<td style="'
                f"padding: 12px 18px;"
                f"vertical-align: middle;"
                f"font-size: 13px;"
                f"{cell_style}"
                f'">{display}</td>'
            )

        body_rows += (
            f'<tr style="'
            f"background: {bg};"
            f"border-bottom: 1px solid rgba(255, 255, 255, 0.04);"
            f"transition: background 0.2s ease;"
            f'" onmouseover="this.style.background=\'rgba(6, 182, 212, 0.08)\'"'
            f' onmouseout="this.style.background=\'{bg}\'"'
            f">{cells}</tr>"
        )

    table_html = f"""
    {title_html}
    <div style="
        overflow-x: auto;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 16px;
    ">
        <table style="
            width: 100%;
            border-collapse: collapse;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            font-size: 14px;
        ">
            <thead>
                <tr style="
                    background: linear-gradient(135deg, #1e293b, #1f2937);
                    border-bottom: 2px solid rgba(6, 182, 212, 0.3);
                ">
                    {header_cells}
                </tr>
            </thead>
            <tbody>
                {body_rows}
            </tbody>
        </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# ALERT TABLE
# ═══════════════════════════════════════════════════════════════════════════

def render_alert_table(alerts_list: Optional[List[Dict]] = None) -> None:
    """
    Render alerts with colored category badges, timestamps, and values.

    Each dict in *alerts_list* should have the keys:
        timestamp, device_id, ispu_value, category (dict), parameter, value

    The *category* dict is expected to contain: label, color, emoji.

    Args:
        alerts_list: List of alert dicts. None or [] shows a success state.
    """
    # ── Empty / no-alerts state ─────────────────────────────────────
    if not alerts_list:
        no_alert_html = """
        <div style="
            background: rgba(34, 197, 94, 0.08);
            border: 1px solid rgba(34, 197, 94, 0.2);
            border-radius: 14px;
            padding: 32px;
            text-align: center;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        ">
            <div style="font-size: 36px; margin-bottom: 10px;">✅</div>
            <p style="
                color: #4ade80;
                font-size: 16px;
                font-weight: 600;
                margin: 0 0 4px 0;
            ">No Active Alerts</p>
            <p style="
                color: #6b7280;
                font-size: 13px;
                margin: 0;
            ">All readings are within safe levels</p>
        </div>
        """
        st.markdown(no_alert_html, unsafe_allow_html=True)
        return

    # ── Column definitions ──────────────────────────────────────────
    columns = ["⏰ Time", "📡 Device", "📊 ISPU", "⚠️ Category", "📝 Parameter", "📈 Value"]

    header_cells = "".join(
        f'<th style="'
        f"padding: 14px 18px;"
        f"text-align: left;"
        f"font-size: 11px;"
        f"font-weight: 600;"
        f"text-transform: uppercase;"
        f"letter-spacing: 0.05em;"
        f"color: #94a3b8;"
        f"white-space: nowrap;"
        f'">{col}</th>'
        for col in columns
    )

    body_rows = ""
    for row_idx, alert in enumerate(alerts_list):
        bg = (
            "rgba(17, 25, 40, 0.5)"
            if row_idx % 2 == 0
            else "rgba(17, 25, 40, 0.25)"
        )

        timestamp = str(alert.get("timestamp", "-"))
        device_id = str(alert.get("device_id", "-"))
        ispu_value = alert.get("ispu_value", 0)
        category = alert.get("category", {})
        parameter = str(alert.get("parameter", "-"))
        value = alert.get("value", "-")

        cat_color = category.get("color", "#6b7280")
        cat_label = category.get("label", "N/A")
        cat_emoji = category.get("emoji", "⚪")

        # Format ISPU value
        if isinstance(ispu_value, float):
            ispu_display = f"{ispu_value:.0f}"
        else:
            ispu_display = str(ispu_value)

        # Format value
        if isinstance(value, float):
            value_display = f"{value:.1f}"
        else:
            value_display = str(value)

        # ISPU cell with colored dot
        ispu_cell = (
            f'<span style="'
            f"display: inline-flex; align-items: center; gap: 8px;"
            f'">'
            f'<span style="'
            f"width: 8px; height: 8px; border-radius: 50%;"
            f"background: {cat_color};"
            f"box-shadow: 0 0 6px {cat_color}66;"
            f"display: inline-block;"
            f'"></span>'
            f'<span style="font-weight: 600; color: #f3f4f6;">'
            f"{ispu_display}</span></span>"
        )

        # Category badge
        category_badge = (
            f'<span style="'
            f"display: inline-flex; align-items: center; gap: 4px;"
            f"background: {cat_color}22;"
            f"color: {cat_color};"
            f"border: 1px solid {cat_color}44;"
            f"border-radius: 999px;"
            f"padding: 4px 12px;"
            f"font-size: 12px;"
            f"font-weight: 600;"
            f"white-space: nowrap;"
            f'">{cat_emoji} {cat_label}</span>'
        )

        cells_html = (
            f'<td style="padding:12px 18px; color:#d1d5db; font-size:13px;">{timestamp}</td>'
            f'<td style="padding:12px 18px; color:#f3f4f6; font-weight:500; font-size:13px;">{device_id}</td>'
            f'<td style="padding:12px 18px; font-size:13px;">{ispu_cell}</td>'
            f'<td style="padding:12px 18px; font-size:13px;">{category_badge}</td>'
            f'<td style="padding:12px 18px; color:#d1d5db; font-size:13px;">{parameter}</td>'
            f'<td style="padding:12px 18px; color:#d1d5db; font-weight:500; font-size:13px;">{value_display}</td>'
        )

        body_rows += (
            f'<tr style="'
            f"background: {bg};"
            f"border-bottom: 1px solid rgba(255, 255, 255, 0.04);"
            f"transition: background 0.2s ease;"
            f'" onmouseover="this.style.background=\'rgba(239, 68, 68, 0.06)\'"'
            f' onmouseout="this.style.background=\'{bg}\'"'
            f">{cells_html}</tr>"
        )

    table_html = f"""
    <div style="
        overflow-x: auto;
        border-radius: 12px;
        border: 1px solid rgba(239, 68, 68, 0.15);
        margin-bottom: 16px;
    ">
        <table style="
            width: 100%;
            border-collapse: collapse;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            font-size: 14px;
        ">
            <thead>
                <tr style="
                    background: linear-gradient(135deg, #2d1b1b, #1f2937);
                    border-bottom: 2px solid rgba(239, 68, 68, 0.3);
                ">
                    {header_cells}
                </tr>
            </thead>
            <tbody>
                {body_rows}
            </tbody>
        </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)
