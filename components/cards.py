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


def render_forecast_summary_card(ispu_predictions: list, current_ispu: float) -> None:
    """
    Render a premium glassmorphic analysis and mitigation card based on forecasted ISPU values.

    Args:
        ispu_predictions: List of forecasted ISPU values.
        current_ispu: The current actual ISPU index value.
    """
    if not ispu_predictions:
        return

    avg_ispu = sum(ispu_predictions) / len(ispu_predictions)
    max_ispu = max(ispu_predictions)
    min_ispu = min(ispu_predictions)

    from utils.helper import get_ispu_category

    # Determine trend compared to current ISPU
    diff = avg_ispu - current_ispu
    if diff > 5.0:
        trend = "Menurun (Polusi Meningkat)"
        trend_color = "#ef4444"  # red
        trend_icon = "📈"
    elif diff < -5.0:
        trend = "Membaik (Polusi Menurun)"
        trend_color = "#22c55e"  # green
        trend_icon = "📉"
    else:
        trend = "Stabil (Relatif Konstan)"
        trend_color = "#3b82f6"  # blue
        trend_icon = "📊"

    worst_category = get_ispu_category(max_ispu)
    cat_color = worst_category.get("color", "#06b6d4")
    cat_label = worst_category.get("label", "Sedang")
    cat_emoji = worst_category.get("emoji", "🟢")

    # Define custom mitigation guidelines based on the peak forecasted ISPU
    if max_ispu <= 50:
        mitigations = [
            "Kualitas udara sangat baik. Aman untuk melakukan semua aktivitas fisik di luar ruangan.",
            "Tutup pintu/jendela tidak diperlukan, ventilasi alami berjalan dengan aman.",
            "Tidak perlu menggunakan masker saat bepergian."
        ]
    elif max_ispu <= 100:
        mitigations = [
            "Kualitas udara dalam kategori Sedang. Mayoritas orang aman beraktivitas di luar.",
            "Bagi individu yang sangat sensitif (misal penderita asma), disarankan membatasi aktivitas fisik berat di luar ruangan.",
            "Pantau kondisi berkala jika polusi udara dirasa mulai mengganggu pernapasan."
        ]
    elif max_ispu <= 200:
        mitigations = [
            "Kualitas udara Tidak Sehat. Kurangi aktivitas luar ruangan yang terlalu lama atau berat.",
            "Gunakan masker standar (seperti N95 atau KF94) bila harus beraktivitas di luar ruangan.",
            "Gunakan pembersih udara (air purifier) di dalam ruangan jika tersedia.",
            "Kelompok sensitif sebaiknya tetap berada di dalam ruangan."
        ]
    elif max_ispu <= 300:
        mitigations = [
            "Kualitas udara Sangat Tidak Sehat. Hindari seluruh aktivitas luar ruangan.",
            "Tutup semua jendela dan pintu rapat-rapat untuk menghindari kontaminasi udara luar.",
            "Nyalakan pembersih udara (air purifier) di dalam rumah.",
            "Gunakan masker respirator medis (N95/KF94) jika sangat terpaksa keluar ruangan."
        ]
    else:
        mitigations = [
            "Tingkat Kualitas Udara Berbahaya! Darurat kesehatan masyarakat.",
            "Hindari aktivitas luar ruangan sama sekali, tetap tinggal di dalam rumah.",
            "Pasang pembersih udara di dalam ruangan dan nyalakan filter udara jika ada.",
            "Gunakan masker pelindung berspesifikasi tinggi jika harus keluar."
        ]

    mitigations_li = "".join([f"<li style='margin-bottom: 8px;'>{item}</li>" for item in mitigations])

    card_html = f"""
    <div style="
        background: linear-gradient(135deg, {cat_color}18, rgba(17, 25, 40, 0.8));
        backdrop-filter: blur(16px) saturate(180%);
        -webkit-backdrop-filter: blur(16px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 6px solid {cat_color};
        border-radius: 20px;
        padding: 28px;
        margin-bottom: 24px;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        color: #ffffff;
    ">
        <!-- Header/Title -->
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 24px;">🔮</span>
                <h3 style="margin: 0; font-size: 1.25rem; font-weight: 700; color: #ffffff;">Analisis & Mitigasi Kualitas Udara Kedepan</h3>
            </div>
            <div style="
                background: {trend_color}20;
                color: {trend_color};
                border: 1px solid {trend_color}44;
                padding: 6px 14px;
                border-radius: 999px;
                font-size: 0.85rem;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 6px;
            ">
                <span>{trend_icon}</span>
                <span>Tren: {trend}</span>
            </div>
        </div>
        
        <!-- Metrics Bar -->
        <div style="display: flex; gap: 16px; margin-bottom: 20px; flex-wrap: wrap;">
            <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); padding: 12px 16px; border-radius: 12px; flex: 1; min-width: 120px;">
                <span style="font-size: 0.75rem; color: #9ca3af; display: block; text-transform: uppercase; margin-bottom: 4px;">Saat Ini</span>
                <span style="font-size: 1.4rem; font-weight: 700; color: #ffffff;">{current_ispu:.1f}</span>
            </div>
            <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); padding: 12px 16px; border-radius: 12px; flex: 1; min-width: 120px;">
                <span style="font-size: 0.75rem; color: #9ca3af; display: block; text-transform: uppercase; margin-bottom: 4px;">Prediksi Rata-rata</span>
                <span style="font-size: 1.4rem; font-weight: 700; color: #ffffff;">{avg_ispu:.1f}</span>
            </div>
            <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); padding: 12px 16px; border-radius: 12px; flex: 1; min-width: 120px; border-left: 3px solid {cat_color};">
                <span style="font-size: 0.75rem; color: #9ca3af; display: block; text-transform: uppercase; margin-bottom: 4px;">Prediksi Puncak</span>
                <span style="font-size: 1.4rem; font-weight: 700; color: {cat_color};">{max_ispu:.1f}</span>
            </div>
        </div>
        
        <!-- Summary & Mitigations -->
        <div>
            <p style="margin: 0 0 16px 0; font-size: 0.95rem; line-height: 1.6; color: #e5e7eb;">
                Dalam 1 jam ke depan, indeks ISPU diprediksi berkisar antara 
                <b style="color: #ffffff;">{min_ispu:.1f}</b> hingga <b style="color: #ffffff;">{max_ispu:.1f}</b>. 
                Puncak polusi diprediksi mencapai kategori <span style="color: {cat_color}; font-weight: 700;">{cat_emoji} {cat_label}</span>.
            </p>
            
            <h4 style="margin: 20px 0 10px 0; font-size: 0.95rem; font-weight: 600; color: {cat_color}; text-transform: uppercase; letter-spacing: 0.05em; display: flex; align-items: center; gap: 6px;">
                <span>🛡️</span> Rekomendasi Tindakan & Mitigasi:
            </h4>
            
            <ul style="margin: 0; padding-left: 20px; font-size: 0.9rem; line-height: 1.6; color: #d1d5db;">
                {mitigations_li}
            </ul>
        </div>
    </div>
    """
    st.markdown(card_html.replace('\n', ' '), unsafe_allow_html=True)

