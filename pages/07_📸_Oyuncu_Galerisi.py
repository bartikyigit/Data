import streamlit as st
import pandas as pd
from config import AGE_GROUPS
from database import db_manager
from styles import inject_styles, page_header, COLORS

st.set_page_config(page_title="Oyuncu Galerisi | TFF", layout="wide")
inject_styles()
page_header("👥", "Oyuncu Galerisi", "Takım kadrosunu, oyuncu fotoğraflarını ve kulüp bilgilerini görüntüleyin")

# ── Üst Seçim Alanı ───────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 3])
with col1:
    age_group = st.selectbox("Yaş Grubu Seçiniz", AGE_GROUPS)

# Veritabanından fotoğraflarla birlikte oyuncuları çekiyoruz
players_info = db_manager.get_players_with_info(age_group)

if not players_info:
    st.warning(f"{age_group} grubu için henüz veritabanında oyuncu bulunmuyor.")
    st.stop()

st.divider()
st.markdown(f"<h3 style='font-family: Bebas Neue; letter-spacing: 1px; color: {COLORS['GRAY_900']};'>"
            f"🇹🇷 {age_group} KADROSU ({len(players_info)} Oyuncu)</h3>", unsafe_allow_html=True)

# ── Oyuncu Kartları CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
.player-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 16px;
    padding: 20px 10px 15px;
    text-align: center;
    box-shadow: 0 4px 10px rgba(0,0,0,0.03);
    transition: all 0.3s ease;
    margin-bottom: 15px;
}
.player-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 12px 20px rgba(227,10,23,0.15);
    border-color: #E30A17;
}
.photo-wrapper {
    position: relative;
    width: 120px;
    height: 120px;
    margin: 0 auto 15px;
}
.player-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 50%;
    border: 3px solid #F3F4F6;
    background: #FAFAFA;
}
.club-badge {
    position: absolute;
    bottom: -4px;
    right: -4px;
    width: 42px;
    height: 42px;
    background: white;
    border-radius: 50%;
    padding: 5px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    border: 1px solid #E5E7EB;
    display: flex;
    align-items: center;
    justify-content: center;
}
.club-badge img {
    width: 100%;
    height: 100%;
    object-fit: contain;
}
.p-name {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 22px;
    color: #111827;
    letter-spacing: 0.5px;
    margin-bottom: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    padding: 0 5px;
}
.p-stat {
    font-size: 11px;
    color: #6B7280;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

# Kayıt girilmemişse kullanılacak varsayılan görseller
DEFAULT_PLAYER = "https://cdn-icons-png.flaticon.com/512/847/847969.png" 
DEFAULT_CLUB   = "https://upload.wikimedia.org/wikipedia/tr/b/b9/Türkiye_Futbol_Federasyonu_logo.png"

# ── Grid Sistemiyle Kartları Dizme ────────────────────────────────────────────
cols_per_row = 5
for i in range(0, len(players_info), cols_per_row):
    cols = st.columns(cols_per_row)
    for j in range(cols_per_row):
        idx = i + j
        if idx < len(players_info):
            p_data = players_info[idx]
            player_name = p_data['name']
            
            # Veritabanında link varsa onu kullan, yoksa Default (TFF) görselini koy
            photo_url = p_data.get('photo_url')
            club_logo_url = p_data.get('club_logo_url')
            
            if not photo_url: photo_url = DEFAULT_PLAYER
            if not club_logo_url: club_logo_url = DEFAULT_CLUB
            
            with cols[j]:
                # Kartın Görsel HTML'i
                st.markdown(f"""
                <div class="player-card">
                    <div class="photo-wrapper">
                        <img class="player-img" src="{photo_url}" alt="{player_name}">
                        <div class="club-badge">
                            <img src="{club_logo_url}" alt="Kulüp">
                        </div>
                    </div>
                    <div class="p-name" title="{player_name}">{player_name}</div>
                    <div class="p-stat">Milli Oyuncu</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Profile Git Butonu
                if st.button("📈 PROFİLE GİT", key=f"btn_{idx}", use_container_width=True):
                    st.session_state['pp_player'] = player_name
                    st.session_state['pp_age'] = age_group
                    st.switch_page("pages/03_Oyuncu_Profili.py")

st.markdown('<div class="tff-footer"><p>Rugby Performans Sistemi · Oyuncu Galerisi</p></div>', unsafe_allow_html=True)