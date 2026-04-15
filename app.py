import streamlit as st
import pandas as pd
import os
from config import AGE_GROUPS, METRICS, PRIMARY_METRICS
from database import db_manager
from styles import inject_styles, sidebar_brand, section_title, page_header, COLORS, info_box

st.set_page_config(
    page_title="Bursaspor Veri Merkezi",
    page_icon="⚽", # Futbol temasına uygun ikon
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_styles()

# ── DİNAMİK DOSYA BULUCU (EMOJİ VE NUMARALARI TEMİZLEYEREK BULUR) ──
def get_exact_page_path(keyword):
    """pages klasöründeki dosyaları tarar ve kelimeyi içeren dosyanın tam yolunu bulur."""
    if os.path.exists("pages"):
        for file in os.listdir("pages"):
            if keyword in file and file.endswith(".py"):
                return f"pages/{file}"
    return None

# ── Sidebar (Kayıt ve Veri Yükleme Yönetimi) ──────────────────────────────────
with st.sidebar:
    sidebar_brand()
    
    st.markdown('<div class="sidebar-label">📂 Sisteme Veri Yükle</div>', unsafe_allow_html=True)
    
    upload_type = st.radio("Yüklenecek Veri Formatı:", 
                           ["GPS / Maç Verisi", "Fiziksel Test (CMJ, Nordic vb.)"],
                           help="Yüklediğiniz Excel'in içeriğini seçin. Yanlış seçim veritabanını bozabilir.")
                           
    uploaded_file = st.file_uploader("Excel Dosyası Yükle", type=['xlsx'], label_visibility='collapsed')
    
    if uploaded_file:
        age_group = st.selectbox("Hedef Takım / Yaş Grubu", AGE_GROUPS, key="upload_age")
        
        test_date = None
        if upload_type == "Fiziksel Test (CMJ, Nordic vb.)":
            test_date = st.date_input("Test Tarihi Seçin", help="Eğer Excel dosyasının içinde 'Date' isminde bir kolon yoksa, buradaki tarih tüm kayıtlara atanır.")

        if st.button("Veritabanına Aktar", use_container_width=True): 
            with st.spinner("Sisteme işleniyor..."):
                if upload_type == "GPS / Maç Verisi":
                    result = db_manager.excel_to_db(uploaded_file, age_group)
                else:
                    date_str = test_date.strftime('%Y-%m-%d')
                    result = db_manager.test_excel_to_db(uploaded_file, age_group, date_str)
                    
                if result['status'] == 'success':
                    st.success(result['message'])
                    st.rerun()
                else:
                    st.error(result['message'])
                    
    st.divider()
    
    st.markdown('<div class="sidebar-label">📊 Sistem Özeti</div>', unsafe_allow_html=True)
    try:
        all_data = db_manager.get_all_data()
        if not all_data.empty:
            c1, c2 = st.columns(2)
            match_data = all_data[all_data['tip'].str.upper()=='MATCH']
            
            # Sidebar Kartları
            with c1:
                st.markdown(f"""
                <div class='tff-stat-card' style='padding:12px; margin-bottom:10px; text-align:center;'>
                    <div class='sc-label' style='margin-top:0;'>Oyuncu</div>
                    <div class='sc-val' style='font-size:22px;'>{all_data['player_name'].nunique()}</div>
                </div>
                <div class='tff-stat-card' style='padding:12px; text-align:center;'>
                    <div class='sc-label' style='margin-top:0;'>Kayıt</div>
                    <div class='sc-val' style='font-size:22px;'>{len(all_data)}</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class='tff-stat-card' style='padding:12px; margin-bottom:10px; text-align:center;'>
                    <div class='sc-label' style='margin-top:0;'>Hafta</div>
                    <div class='sc-val' style='font-size:22px;'>{all_data['camp_id'].nunique()}</div>
                </div>
                <div class='tff-stat-card' style='padding:12px; text-align:center;'>
                    <div class='sc-label' style='margin-top:0;'>Maç Günü</div>
                    <div class='sc-val' style='font-size:22px;'>{match_data['tarih'].nunique() if not match_data.empty else 0}</div>
                </div>
                """, unsafe_allow_html=True)
    except:
        pass

# ── Header ────────────────────────────────────────────────────────────────────
page_header("⚽", "Bursaspor Veri Merkezi",
            "A Takım ve Akademi Atletik Performans Sistemi")

info_box("Sisteme hoş geldiniz. Bu sayfa, yüklenen tüm takımlara ait genel verilerin özetini ve oyuncuların haftalık katılım oranlarını gösterir. Detaylı analizler için aşağıdaki menüleri kullanabilirsiniz.")

# ── Nav Kartları ─────────────────────────
nav_items = [
    ("Kamp_Analizi",        "🏃‍♂️", "Hafta Analizi",    "Günlük & hafta bazlı sıralamalar"),
    ("Oyuncu_Profili",      "👤", "Oyuncu Profili",  "Bireysel performans & radar"),
    ("Karsilastirma",       "⚔️", "Karşılaştırma",   "H2H · Gün · Hafta karşılaştırma"),
    ("Siralamalar",         "📊", "Sıralamalar",     "Günlük · Hafta · Percentile skor"),
    ("Scatter",             "🎯", "Dağılım Analizi", "İki metrik bazlı oyuncu dağılımı"),
    ("Testler",             "🏋️‍♂️", "Fiziksel Testler", "Kuvvet & Sıçrama Laboratuvarı") 
]

cols = st.columns(6) 
for i, (keyword, icon, title, desc) in enumerate(nav_items):
    with cols[i]:
        active = (keyword == "Testler") 
        border = COLORS['GREEN'] if active else COLORS['GRAY_300'] # RED yerine GREEN yapıldı
        shadow = "0 4px 16px rgba(0,122,51,0.15)" if active else "0 1px 4px rgba(0,0,0,0.05)" # Kırmızı gölge Yeşile çevrildi
        st.markdown(f"""
        <div style="background:white;border:2px solid {border};border-radius:14px;
                    padding:15px 5px 10px;text-align:center;box-shadow:{shadow};
                    height:130px;transition:all 0.2s;">
            <div style="font-size:24px;margin-bottom:5px;">{icon}</div>
            <div style="font-family:'Bebas Neue',sans-serif;font-size:15px;letter-spacing:1px;
                        color:{COLORS['GRAY_900']}; line-height:1.1;">{title}</div>
            <div style="font-size:10px;color:{COLORS['GRAY_500']};margin-top:6px; line-height:1.2;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Git →", key=f"nav_{i}", use_container_width=True):
            target_page = get_exact_page_path(keyword)
            if target_page:
                st.switch_page(target_page)
            else:
                st.error(f"'{title}' sayfası bulunamadı!")

st.divider()

# ── Ana İçerik ────────────────────────────────────────────────────────────────
try:
    all_data = db_manager.get_all_data()
    if not all_data.empty:
        # Yaş grubu kartları 
        section_title("Takım Durumları", "📈")
        ag_cols = st.columns(len(AGE_GROUPS))
        for i, ag in enumerate(AGE_GROUPS):
            ag_data = all_data[all_data['age_group'] == ag]
            has = not ag_data.empty
            with ag_cols[i]:
                pc = ag_data['player_name'].nunique() if has else 0
                cc = ag_data['camp_id'].nunique()     if has else 0
                rc = len(ag_data)                     if has else 0
                
                border_color = COLORS['GREEN'] if has else COLORS['GRAY_300'] # RED yerine GREEN
                opacity = "1" if has else "0.5"
                
                st.markdown(f"""
                <div class='tff-stat-card' style='padding:15px; text-align:center; border-top: 4px solid {border_color}; opacity: {opacity};'>
                    <div style='font-family:"Bebas Neue",sans-serif; font-size:28px; color:{COLORS["GRAY_800"]};'>{ag}</div>
                    <div style='font-size:13px; font-weight:700; color:{COLORS["GRAY_600"]}; margin-top:4px;'>{pc} Oyuncu · {cc} Hafta</div>
                    <div style='font-size:11px; color:{COLORS["GRAY_400"]}; margin-top:6px;'>{rc} Kayıt</div>
                </div>
                """, unsafe_allow_html=True)
                
                if has:
                    st.write("")
                    if st.button(f"📊 {ag} ANALİZ ET", key=f"btn_ag_{ag}", use_container_width=True):
                        st.session_state.selected_age_group = ag
                        
                        target_page = get_exact_page_path("Kamp_Analizi")
                        if target_page:
                            st.switch_page(target_page)
                        else:
                            st.error("Analiz sayfası bulunamadı!")

        st.divider()

        # KPI satırı 
        section_title("Genel İstatistikler", "📊")
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        match_df = all_data[all_data['tip'].str.upper()=='MATCH']
        
        def render_kpi_card(title, value, unit=""):
            unit_html = f"<span style='font-size:14px; color:{COLORS['GRAY_400']}; margin-left:4px;'>{unit}</span>" if unit else ""
            return f"""
            <div style="background:white; border:1px solid {COLORS['GRAY_300']}; border-radius:12px; 
                        padding:16px 20px; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.03); 
                        transition:all 0.3s ease;" 
                 onmouseover="this.style.borderColor='{COLORS['GREEN']}'; this.style.transform='translateY(-2px)';" 
                 onmouseout="this.style.borderColor='{COLORS['GRAY_300']}'; this.style.transform='translateY(0)';">
                <div style="font-family:'DM Sans',sans-serif; font-size:11px; font-weight:800; 
                            text-transform:uppercase; letter-spacing:1px; color:{COLORS['GRAY_500']}; margin-bottom:8px;">
                    {title}
                </div>
                <div style="font-family:'Bebas Neue',sans-serif; font-size:32px; color:{COLORS['GRAY_900']}; line-height:1;">
                    {value}{unit_html}
                </div>
            </div>
            """

        with k1: st.markdown(render_kpi_card("Toplam Oyuncu", all_data['player_name'].nunique()), unsafe_allow_html=True)
        with k2: st.markdown(render_kpi_card("Toplam Hafta", all_data['camp_id'].nunique()), unsafe_allow_html=True)
        with k3: st.markdown(render_kpi_card("Toplam Kayıt", len(all_data)), unsafe_allow_html=True)
        with k4: st.markdown(render_kpi_card("Toplam Maç Günü", match_df['tarih'].nunique() if not match_df.empty else 0), unsafe_allow_html=True)
        with k5: st.markdown(render_kpi_card("Ort. Mesafe", f"{all_data['total_distance'].mean():.0f}", "m"), unsafe_allow_html=True)
        with k6: st.markdown(render_kpi_card("Max Hız (Genel)", f"{all_data['smax_kmh'].max():.1f}", "km/h"), unsafe_allow_html=True)

        st.divider()

        tbl_col1, tbl_col2 = st.columns(2)
        
        with tbl_col1:
            section_title("🏆 Tüm Takımlar: En Yüksek 10 Performans", "🏃‍♂️")
            
            top10_metric = st.selectbox(
                "Sıralanacak Metriği Seçin", 
                PRIMARY_METRICS, 
                format_func=lambda x: METRICS.get(x, {}).get('display', x).upper(),
                key="home_top10_metric"
            )
            
            if top10_metric in all_data.columns:
                top10 = all_data.nlargest(10, top10_metric)[
                    ['player_name', 'age_group', 'tarih', 'tip', top10_metric]
                ].copy()
                
                top10['tarih'] = top10['tarih'].dt.strftime('%d.%m.%Y')
                
                m_info = METRICS.get(top10_metric, {})
                metric_col_name = f"{m_info.get('display', top10_metric)} ({m_info.get('unit', '')})"
                
                top10.columns  = ['Oyuncu', 'Takım', 'Tarih', 'Seans Tipi', metric_col_name]
                
                st.dataframe(top10, width='stretch', hide_index=True, height=350)
            else:
                st.warning("Seçilen metrik için sistemde veri bulunamadı.")

        with tbl_col2:
            section_title("Tüm Oyuncuların Katılım Raporu", "📅")
            
            temp_data = all_data.copy()
            temp_data['tip'] = temp_data['tip'].fillna('')
            temp_data['is_match'] = temp_data['tip'].str.upper().str.contains('MATCH').astype(int)
            temp_data['is_training'] = temp_data['tip'].str.upper().str.contains('TRAINING').astype(int)
            
            camp_leaders = temp_data.groupby(['player_name', 'age_group']).agg(
                Hafta_Sayisi=('camp_id', 'nunique'),
                Seans_Sayisi=('tarih', 'count'),
                Mac_Sayisi=('is_match', 'sum'),
                Antrenman_Sayisi=('is_training', 'sum')
            ).reset_index()
            
            camp_leaders = camp_leaders.sort_values(by=['Hafta_Sayisi', 'Mac_Sayisi', 'Antrenman_Sayisi'], ascending=[False, False, False]).copy()
            camp_leaders.columns = ['Oyuncu', 'Takım', 'Hafta', 'Toplam Seans', 'Maç', 'Antrenman']
            st.dataframe(camp_leaders, width='stretch', hide_index=True, height=350)

    else:
        st.markdown(f"""
        <div style="text-align:center;padding:80px 20px;background:{COLORS['GRAY_50']};
                    border-radius:16px;border:2px dashed {COLORS['GRAY_300']};margin-top:20px;">
            <div style="font-size:52px;margin-bottom:16px;">📂</div>
            <div style="font-family:'Bebas Neue',sans-serif;font-size:30px;letter-spacing:2px;
                        color:{COLORS['GRAY_700']};">HENÜZ VERİ YÜKLENMEDİ</div>
            <div style="font-size:13px;color:{COLORS['GRAY_400']};margin-top:8px;">
                Sol panelden Excel dosyanızı yükleyerek sistemi başlatın</div>
        </div>
        """, unsafe_allow_html=True)
except Exception as e:
    st.error(f"Hata: {e}")

st.markdown("""
<div class="tff-footer">
    <p><strong>Bursaspor Veri Merkezi</strong> · A Takım ve Akademi Atletik Performans Sistemi</p>
</div>""", unsafe_allow_html=True)