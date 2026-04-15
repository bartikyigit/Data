import streamlit as st
import pandas as pd
from database import db_manager
from styles import inject_styles, page_header, COLORS

st.set_page_config(page_title="Oyuncu Arama | TFF", layout="wide")
inject_styles()

page_header("🔍", "OYUNCU REHBERİ", "Tüm yaş grupları arasında hızlı ve dinamik arama yapın.")

# ── Veriyi Caching ile Optimize Et ───────────────────────────────────────────
@st.cache_data(ttl=600)
def load_search_data():
    df = db_manager.get_all_data()
    if df.empty:
        return pd.DataFrame()
    
    # Oyuncu bazlı özet: En son yaş grubu, toplam kamp ve toplam seans
    summary = df.groupby('player_name').agg({
        'age_group': 'last',
        'camp_id': 'nunique',
        'tarih': 'count'
    }).reset_index()
    summary.columns = ['Name', 'Last_Age', 'Camp_Count', 'Session_Count']
    return summary

player_data = load_search_data()

# ── Dinamik Arama Alanı ──────────────────────────────────────────────────────
# CSS ile arama kutusuna biraz daha "modern" bir hava katıyoruz
st.markdown("""
<style>
    .stTextInput > div > div > input {
        border-radius: 25px;
        padding: 15px 25px;
        border: 2px solid #E5E7EB;
        font-size: 18px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #E30A17;
        box-shadow: 0 0 10px rgba(227,10,23,0.1);
    }
</style>
""", unsafe_allow_html=True)

query = st.text_input("", placeholder="🔍 Oyuncu adı veya soyadı yazmaya başlayın...", key="global_search")

# ── Filtreleme Mantığı ───────────────────────────────────────────────────────
if query:
    # Arama terimine göre filtrele (Harf duyarsız)
    filtered = player_data[player_data['Name'].str.contains(query, case=False, na=False)]
    
    if not filtered.empty:
        st.write(f"🔍 **{len(filtered)}** sonuç bulundu.")
        st.write("")
        
        for _, row in filtered.iterrows():
            p_name = row['Name']
            p_info = db_manager.get_player_info(p_name)
            
            # Kart Görünümü
            with st.container():
                # HTML/CSS ile şık bir liste elemanı oluşturuyoruz
                st.markdown(f"""
                <div style="
                    background: white; 
                    border: 1px solid {COLORS['GRAY_200']}; 
                    border-left: 5px solid {COLORS['GREEN']}; 
                    border-radius: 12px; 
                    padding: 15px 25px; 
                    margin-bottom: 12px; 
                    display: flex; 
                    align-items: center; 
                    justify-content: space-between;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.02);
                    transition: transform 0.2s;
                ">
                    <div style="display: flex; align-items: center; gap: 20px;">
                        <img src="{p_info.get('photo_url') or 'https://cdn-icons-png.flaticon.com/512/847/847969.png'}" 
                             style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover; background: #f9fafb; border: 1px solid #eee;">
                        <div>
                            <div style="font-family: 'Bebas Neue'; font-size: 24px; color: {COLORS['GRAY_900']}; letter-spacing: 1px;">
                                {p_name.upper()}
                            </div>
                            <div style="font-size: 13px; font-weight: 700; color: {COLORS['GRAY_500']}; text-transform: uppercase;">
                                🇹🇷 {row['Last_Age']} MİLLİ TAKIMI &nbsp;·&nbsp; 
                                <span style="color: {COLORS['GREEN']}">{row['Camp_Count']} KAMP</span> &nbsp;·&nbsp; 
                                {row['Session_Count']} SEANS
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Butonu kartın altına ama sağa yaslı koyalım
                c1, c2 = st.columns([5, 1])
                with c2:
                    if st.button("PROFİLİ AÇ ➔", key=f"btn_{p_name}", use_container_width=True):
                        st.session_state['pp_player'] = p_name
                        st.session_state['pp_age'] = row['Last_Age']
                        st.switch_page("pages/03_Oyuncu_Profili.py")
                st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    else:
        st.info("Eşleşen bir oyuncu bulunamadı.")
else:
    # Arama yapılmadığında gösterilecek boş durum veya son aramalar
    st.markdown(f"""
    <div style="text-align: center; padding: 50px; color: {COLORS['GRAY_400']};">
        <div style="font-size: 60px;">⚽</div>
        <div style="font-family: 'Bebas Neue'; font-size: 30px; margin-top: 15px;">Hızlı Oyuncu Sorgulama Sistemi</div>
        <p>İsim yazmaya başladığınızda sonuçlar anlık olarak burada listelenir.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="tff-footer"><p>RUGBY Bilgi Sistemi</p></div>', unsafe_allow_html=True)