import streamlit as st
from config import COLORS, POSITIONS

def player_card(name, age_group, stats, photo_url=None):
    """Oyuncu kartı"""
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if photo_url:
            st.image(photo_url, width=80)
        else:
            st.markdown(f'<div style="font-size: 60px; text-align: center;">👤</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"**{name}**")
        st.caption(f"{age_group}")
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Kamplar", stats.get('camp_count', 0))
        with col_b:
            st.metric("Seanslar", stats.get('session_count', 0))

def metric_comparison(label, value1, value2, unit=""):
    """Metrik karşılaştırması"""
    if value1 > value2:
        color = COLORS['WIN']
        icon = "✅"
    elif value1 < value2:
        color = COLORS['LOSS']
        icon = "❌"
    else:
        color = COLORS['TIE']
        icon = "⚖️"
    
    st.markdown(f"""
    <div style="background: white; padding: 12px; border-left: 4px solid {color}; border-radius: 6px;">
        <div style="font-size: 12px; color: #666;">{label}</div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 8px;">
            <div style="text-align: center; background: #f5f5f5; padding: 8px; border-radius: 4px;">
                <div style="font-weight: bold; font-size: 14px;">{value1:.1f}</div>
            </div>
            <div style="text-align: center; background: #f5f5f5; padding: 8px; border-radius: 4px;">
                <div style="font-weight: bold; font-size: 14px;">{value2:.1f}</div>
            </div>
        </div>
        <div style="text-align: center; margin-top: 6px; font-size: 11px; color: {color};">
            {icon} {abs(value1 - value2):.1f} {unit}
        </div>
    </div>
    """, unsafe_allow_html=True)

def percentile_color_badge(value):
    """Percentile renk badge'i"""
    if value >= 80:
        color = COLORS['EXCELLENT']
        label = "Çok İyi"
    elif value >= 65:
        color = COLORS['GOOD']
        label = "İyi"
    elif value >= 50:
        color = COLORS['MEDIUM']
        label = "Orta"
    else:
        color = COLORS['LOW']
        label = "Düşük"
    
    return color, label