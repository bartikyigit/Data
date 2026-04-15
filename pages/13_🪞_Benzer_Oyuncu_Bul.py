import streamlit as st
import pandas as pd
from database import db_manager
from styles import inject_styles, page_header, section_title, COLORS
from utils import find_similar_players, plot_dual_radar

st.set_page_config(page_title="Benzer Oyuncu Bul | TFF", layout="wide")
inject_styles()

page_header("🔍", "FİZİKSEL PROFİL EŞLEŞTİRME (BENZER OYUNCU MOTORU)", 
            "Tüm veritabanını tarayarak fiziksel performans metriklerine göre çok boyutlu oyuncu eşleştirme motoru.")

# ── 1. VERİ HAZIRLIĞI (TÜM OYUNCULARI ÇEKME) ──────────────────────────────────
@st.cache_data(ttl=600)
def get_all_data():
    return db_manager.get_all_data()

all_data = get_all_data()

if all_data.empty:
    st.warning("Sistemde analiz edilecek kayıtlı veri bulunmamaktadır.")
    st.stop()

# Analiz için kritik 6 ana metrik (Vektör bileşenleri)
analysis_metrics = ['total_distance', 'smax_kmh', 'dist_25_plus', 'player_load', 'amp', 'metrage']

# ── 2. OYUNCU SEÇİMİ VE SONUÇ FİLTRELERİ ──────────────────────────────────────
st.markdown("<div style='background:#FAFAFA; padding:20px; border-radius:12px; border:1px solid #e5e7eb; margin-bottom:25px;'>", unsafe_allow_html=True)
col_sel1, col_sel2, col_sel3 = st.columns([2, 1, 2])

# Seçim ve Filtreleme İşlemleri
player_list = sorted(all_data['player_name'].unique())
all_ages = sorted(all_data['age_group'].dropna().unique().tolist())

with col_sel1:
    target_player = st.selectbox("REFERANS (HEDEF) OYUNCU SEÇİN", player_list, key="sim_target",
                                 help="Karakteristik özelliklerine en yakın diğer oyuncuları bulmak istediğiniz ismi seçin.")

with col_sel2:
    # Veri Temizliği: Antrenman mı Maç verisi mi?
    ses_filter = st.multiselect("İNCELENECEK SEANS TİPİ", ["TRAINING", "MATCH"], default=["MATCH"], key="sim_ses",
                                help="Daha doğru bir kıyaslama için sadece Maç veya sadece Antrenman verilerini baz alabilirsiniz.")

with col_sel3:
    # AÇIKLAMA: Sonuçları filtrelemek için çoklu yaş grubu seçimi (Multi-Select)
    target_age_pools = st.multiselect("SONUÇLARI FİLTRELE (YAŞ GRUBU)", all_ages, default=all_ages, key="sim_pool",
                                      help="Sistem tüm oyuncularda benzerlik hesaplar, ancak sadece burada seçtiğiniz yaş gruplarındaki oyuncuları listeler.")

st.markdown("</div>", unsafe_allow_html=True)

# ── 3. VERİ UYARLAMA VE HESAPLAMA MOTORU ───────────────────────────────────────
# Sadece seçilen seans tiplerini içeren bir havuz oluştur
session_data = all_data.copy()

if ses_filter:
    session_data = session_data[session_data['tip'].isin(ses_filter)]

# Hata Kontrolü: Seçilen oyuncunun bu seans tipinde verisi var mı?
if session_data[session_data['player_name'] == target_player].empty:
    st.error(f"Seçilen seans filtrelerinde ({', '.join(ses_filter)}) referans oyuncu {target_player} için yeterli veri yok.")
    st.stop()

# utils.py içindeki algoritmaya tüm session verisini gönderiyoruz
# (Algoritma tüm oyuncuları tarar ve benzerlik skorlarını oluşturur)
sim_results = find_similar_players(target_player, session_data, analysis_metrics)

if sim_results is not None and not sim_results.empty:
    
    # ── 4. SONUÇ FİLTRELEME (RESULT FILTERING) ─────────────────────────────────
    # sim_results tablosuna oyuncuların yaş gruplarını ekleyelim ki filtreleyebilelim
    player_ages = all_data[['player_name', 'age_group']].drop_duplicates()
    sim_results = sim_results.merge(player_ages, left_on='OYUNCU', right_on='player_name', how='left')
    
    # Hedef oyuncunun kendisini sonuçlardan çıkart
    sim_results = sim_results[sim_results['OYUNCU'] != target_player]
    
    # Kullanıcının seçtiği yaş gruplarına göre eşleşmeleri filtrele
    if target_age_pools:
        sim_results = sim_results[sim_results['age_group'].isin(target_age_pools)]
        
    # ── 5. GÖRSELLEŞTİRME VE LİSTELEME ─────────────────────────────────────────
    if not sim_results.empty:
        res_col, viz_col = st.columns([1, 2])
        
        with res_col:
            section_title("BENZERLİK SKORLARI", "🧬")
            st.markdown(f"<p style='color:gray; font-size:13px;'><b>{target_player}</b> profiline en yakın fiziksel eşleşmeler (Sıralı):</p>", unsafe_allow_html=True)
            
            # Filtrelenmiş sonuçların en yakın ilk 5 kişisini al
            top_n = sim_results.head(5)
            for idx, row in top_n.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div style='background:white; padding:15px; border-radius:12px; border-left:6px solid {COLORS['RED']}; box-shadow: 0 3px 6px rgba(0,0,0,0.05); margin-bottom:12px;'>
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <div style='font-family: Bebas Neue; font-size:18px; color:{COLORS['GRAY_900']}'>{row['OYUNCU']}</div>
                            <span style='background:#F3F4F6; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:bold; color:{COLORS['GRAY_600']}'>{row['age_group']}</span>
                        </div>
                        <div style='color:{COLORS['GRAY_500']}; font-size:12px; font-weight:bold; margin-top:5px;'>PROFIL EŞLEŞMESİ: %{row['BENZERLİK (%)']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    # Streamlit progress bar %100 üzerinden 1.0 skalasında çalışır
                    st.progress(row['BENZERLİK (%)'] / 100)

        with viz_col:
            most_similar = top_n.iloc[0]['OYUNCU']
            most_similar_age = top_n.iloc[0]['age_group']
            section_title(f"KIYASLAMA ANALİZİ: {target_player} VS {most_similar}", "⚖️")
            st.markdown("<p style='font-size:12px; color:gray;'>Aşağıdaki radar grafiği, iki oyuncunun ortalama performanslarını Z-Skoru (Genel Popülasyon Medyanı) bazında karşılaştırır.</p>", unsafe_allow_html=True)
            
            # İki oyuncunun verilerini çek
            p1_data = session_data[session_data['player_name'] == target_player]
            p2_data = session_data[session_data['player_name'] == most_similar]
            
            # Karşılaştırmalı Radar (utils.py'den gelir)
            fig = plot_dual_radar(target_player, p1_data, f"{most_similar} ({most_similar_age})", p2_data, analysis_metrics)
            if fig:
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("Radar grafiği oluşturulabilmesi için verilerin istatistiksel geçerliliği sağlanamadı.")
    else:
        st.info("Seçtiğiniz yaş gruplarında eşleşecek benzer bir profil bulunamadı.")
else:
    st.info("Yeterli veri sağlanamadığı için analiz gerçekleştirilemedi.")

# ── 6. TEKNİK METODOLOJİ (Ayrıntılı İstatistiksel Açıklama) ───────────────────
st.divider()
with st.expander("🔬 BU ANALİZ NASIL ÇALIŞIYOR? (MATEMATİKSEL METODOLOJİ)", expanded=False):
    st.markdown("""
    ### İstatistiksel Yaklaşım: Kosinüs Benzerliği (Cosine Similarity)
    
    Bu ekran, oyuncuları sadece "en çok koşanlar" olarak sıralamak yerine, performanslarının **karakteristik oranlarını** analiz eder. 
    Bir Scouting (Yetenek Keşfi) aracı olarak, oyuncunun oyun tarzını (stilini) matematiksel bir vektöre dönüştürür.
    
    #### 1. Çok Boyutlu Özellik Vektörleri
    Analiz edilen her bir metrik (Mesafe, Hız, Sprint vb.), her oyuncu için bir boyut oluşturur. 6 ana metrik kullandığımız için her oyuncu 6 boyutlu bir uzayda bir **vektör (ok)** olarak temsil edilir.
    
    #### 2. Min-Max Normalizasyonu (Feature Scaling)
    Metriklerin ölçekleri birbirinden çok farklıdır (Mesafe metre cinsinden 10.000 iken, Hız km/h cinsinden 30'dur). Benzerlik hesaplanmadan önce tüm değerler $0$ ile $1$ arasına sıkıştırılır (Standardizasyon). Böylece hiçbir yüksek hacimli metrik (örn: Mesafe), düşük hacimli ancak kritik bir metriği (örn: İvmelenme) istatistiksel olarak baskılayamaz.
    
    #### 3. Açısal Mesafe Hesaplaması
    Algoritma, iki oyuncunun vektörleri arasındaki açının kosinüsünü hesaplar. İki vektör arasındaki açı ne kadar küçükse (ve kosinüs değeri 1'e ne kadar yakınsa), oyuncuların profil oranları o kadar benzerdir.
    
    **Matematiksel Formül:**
    """)
    
    # LaTeX kullanımı - Display equation
    st.latex(r"\text{Similarity (Benzerlik)} = \cos(\theta) = \frac{\mathbf{A} \cdot \mathbf{B}}{\|\mathbf{A}\| \|\mathbf{B}\|}")
    
    st.markdown("""
    #### Neden Öklid Uzaklığı (Euclidean Distance) Değil?
    Öklid uzaklığı sadece "miktar" farkına bakar. Ancak bir oyuncu maçta 90 dakika, diğeri (alt yaş grubunda) 45 dakika oynamış olsa bile, **Kosinüs Benzerliği** bu iki oyuncunun performans metriklerinin birbirine olan **oranlarını** yakaladığı için benzer profilleri (oyun tarzlarını) tespit edebilir.
    
    * **%100 Skoru:** İki oyuncunun tüm fiziksel parametrelerinin birbirine mükemmel bir oranda paralel (aynı doğrultuda) olduğunu ifade eder.
    """)

st.markdown('<div class="tff-footer"><p>Rugby Performans Sistemi · Scouting ve Yetenek Eşleştirme Motoru</p></div>', unsafe_allow_html=True)