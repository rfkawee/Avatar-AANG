"""
Cards Component
Renders premium glassmorphism metric cards, ISPU status cards,
and colored status badges for the AirSense dashboard.
"""
import textwrap
import streamlit as st


def render_metric_card(
    title: str,
    value,
    unit: str,
    icon: str,
    delta=None,
    color: str = None,
) -> None:
    """
    Render a single KPI metric card with glassmorphism styling.

    Args:
        title: Card title (e.g., "Temperature").
        value: The metric value to display.
        unit: Unit string (e.g., "°C", "µg/m³").
        icon: Emoji icon for the card.
        delta: Optional delta value (positive = green ▲, negative = red ▼).
        color: Accent color hex string. Defaults to cyan '#06b6d4'.
    """
    if color is None:
        color = "#06b6d4"

    # Format value
    if isinstance(value, float):
        display_value = f"{value:.1f}"
    else:
        display_value = str(value)

    # Build delta HTML
    delta_html = ""
    if delta is not None:
        try:
            delta_num = float(delta)
            if delta_num >= 0:
                delta_arrow = "▲"
                delta_color = "#4ade80"
                delta_sign = "+"
            else:
                delta_arrow = "▼"
                delta_color = "#f87171"
                delta_sign = ""
            delta_html = textwrap.dedent(f"""
            <div style="
                display: inline-flex;
                align-items: center;
                gap: 4px;
                margin-top: 8px;
                padding: 3px 10px;
                border-radius: 8px;
                background: {delta_color}15;
                font-size: 12px;
                font-weight: 600;
                color: {delta_color};
            ">
                <span>{delta_arrow}</span>
                <span>{delta_sign}{delta_num:.1f}</span>
            </div>
            """)
        except (ValueError, TypeError):
            pass

    card_html = textwrap.dedent(f"""
    <div style="
        background: rgba(17, 25, 40, 0.75);
        backdrop-filter: blur(16px) saturate(180%);
        -webkit-backdrop-filter: blur(16px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 4px solid {color};
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 12px;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
        cursor: default;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    " onmouseover="
        this.style.transform='translateY(-2px) scale(1.02)';
        this.style.boxShadow='0 8px 32px {color}22, 0 0 20px {color}11';
        this.style.borderColor='rgba(255,255,255,0.15)';
    " onmouseout="
        this.style.transform='translateY(0) scale(1)';
        this.style.boxShadow='none';
        this.style.borderColor='rgba(255,255,255,0.08)';
    ">
        <!-- Subtle gradient overlay -->
        <div style="
            position: absolute;
            top: 0; right: 0;
            width: 120px; height: 120px;
            background: radial-gradient(circle, {color}08 0%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
        "></div>

        <!-- Icon -->
        <div style="font-size: 32px; margin-bottom: 12px; line-height: 1;">
            {icon}
        </div>

        <!-- Title -->
        <p style="
            margin: 0 0 8px 0;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #9ca3af;
        ">{title}</p>

        <!-- Value -->
        <div style="display: flex; align-items: baseline; gap: 6px;">
            <span style="
                font-size: 36px;
                font-weight: 800;
                color: #ffffff;
                line-height: 1;
                letter-spacing: -1px;
            ">{display_value}</span>
            <span style="
                font-size: 16px;
                font-weight: 500;
                color: #6b7280;
            ">{unit}</span>
        </div>

        <!-- Delta -->
        {delta_html}
    </div>
    """)
    st.markdown(card_html.replace('\n', ' '), unsafe_allow_html=True)


def render_ispu_card(ispu_value: float, category_dict: dict) -> None:
    """
    Render a large ISPU status card with category-colored gradient background.

    Args:
        ispu_value: The calculated ISPU index value.
        category_dict: Dict with keys: label, label_en, min, max, color, emoji, recommendation.
    """
    cat_color = category_dict.get("color", "#06b6d4")
    cat_emoji = category_dict.get("emoji", "⚪")
    cat_label = category_dict.get("label", "N/A")
    cat_label_en = category_dict.get("label_en", "")
    cat_recommendation = category_dict.get("recommendation", "")
    cat_max = category_dict.get("max", 500)

    # Calculate progress (0-500 scale)
    progress_pct = min((ispu_value / 500) * 100, 100)

    # Format ISPU value
    if isinstance(ispu_value, float):
        display_ispu = f"{ispu_value:.0f}"
    else:
        display_ispu = str(ispu_value)

    # Inject keyframes animation
    anim_css = """
    <style>
    @keyframes ispu-pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }
    @keyframes ispu-glow {
        0%, 100% { filter: drop-shadow(0 0 8px currentColor); }
        50% { filter: drop-shadow(0 0 16px currentColor); }
    }
    @keyframes shimmer {
        0% { background-position: -200% center; }
        100% { background-position: 200% center; }
    }
    </style>
    """
    st.markdown(anim_css.replace('\n', ' '), unsafe_allow_html=True)

    card_html = textwrap.dedent(f"""
    <div style="
        background: linear-gradient(135deg, {cat_color}25, {cat_color}08, rgba(17, 25, 40, 0.9));
        border: 2px solid {cat_color}55;
        border-radius: 20px;
        padding: 32px;
        text-align: center;
        position: relative;
        overflow: hidden;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        margin-bottom: 16px;
    ">
        <!-- Background glow -->
        <div style="
            position: absolute;
            top: -50%; left: -50%;
            width: 200%; height: 200%;
            background: radial-gradient(circle at center, {cat_color}0a 0%, transparent 50%);
            pointer-events: none;
        "></div>

        <!-- Emoji -->
        <div style="
            font-size: 48px;
            margin-bottom: 12px;
            animation: ispu-pulse 2.5s ease-in-out infinite;
            display: inline-block;
        ">{cat_emoji}</div>

        <!-- ISPU Value -->
        <div style="
            font-size: 64px;
            font-weight: 800;
            color: #ffffff;
            line-height: 1;
            letter-spacing: -2px;
            margin-bottom: 8px;
            text-shadow: 0 0 30px {cat_color}44;
        ">{display_ispu}</div>

        <!-- Category Labels -->
        <div style="
            font-size: 20px;
            font-weight: 700;
            color: {cat_color};
            margin-bottom: 2px;
        ">{cat_label}</div>
        <div style="
            font-size: 14px;
            font-weight: 500;
            color: #9ca3af;
            margin-bottom: 20px;
        ">{cat_label_en}</div>

        <!-- Progress bar -->
        <div style="
            background: rgba(255, 255, 255, 0.06);
            border-radius: 8px;
            height: 8px;
            width: 100%;
            margin-bottom: 20px;
            overflow: hidden;
        ">
            <div style="
                background: linear-gradient(90deg, {cat_color}, {cat_color}cc);
                height: 100%;
                width: {progress_pct}%;
                border-radius: 8px;
                transition: width 1s ease;
                box-shadow: 0 0 10px {cat_color}44;
            "></div>
        </div>

        <!-- Scale labels -->
        <div style="
            display: flex;
            justify-content: space-between;
            font-size: 10px;
            color: #6b7280;
            margin-bottom: 20px;
            padding: 0 4px;
        ">
            <span>0</span>
            <span>100</span>
            <span>200</span>
            <span>300</span>
            <span>400</span>
            <span>500</span>
        </div>

        <!-- Divider -->
        <hr style="
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, {cat_color}33, transparent);
            margin: 0 0 16px 0;
        "/>

        <!-- Recommendation -->
        <p style="
            font-size: 13px;
            color: #9ca3af;
            line-height: 1.6;
            margin: 0;
            padding: 0 8px;
        ">💡 {cat_recommendation}</p>
    </div>
    """)
    st.markdown(card_html.replace('\n', ' '), unsafe_allow_html=True)


def render_status_badge(text: str, color: str) -> None:
    """
    Render a small colored pill badge.

    Args:
        text: Badge text content.
        color: Hex color string for the badge.
    """
    badge_html = textwrap.dedent(f"""
    <span style="
        display: inline-flex;
        align-items: center;
        background: {color}22;
        color: {color};
        border: 1px solid {color}44;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        letter-spacing: 0.02em;
        white-space: nowrap;
    ">{text}</span>
    """)
    st.markdown(badge_html.replace('\n', ' '), unsafe_allow_html=True)
