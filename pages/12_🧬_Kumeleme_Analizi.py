import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from database import db_manager
from config import PRIMARY_METRICS, METRICS
from styles import inject_styles, page_header, section_title, COLORS, info_box

st.set_page_config(page_title="Kümeleme Analizi | TFF", page_icon="🧠", layout="wide")
inject_styles()

page_header("🧠", "YAPAY ZEKA İLE OYUNCU PROFİLLEME (KÜMELEME ANALİZİ)", 
            "Tüm yaş gruplarındaki oyuncuları atletik performans profillerine göre otomatik olarak gruplandırın.")

# ── MODEL METODOLOJİSİ (Ayrıntılı İstatistiksel Açıklama) ──────────────────────
# AÇIKLAMA: Antrenörlerin makine öğrenmesinin (Unsupervised Learning) nasıl çalıştığını 
# anlaması için eklenmiş kapsamlı spor bilimi notu.
with st.expander("📌 YAPAY ZEKA PROFİLLEME MODELİ: SİSTEM NASIL ÇALIŞIR?", expanded=False):
    st.markdown("""
    **Kümeleme (Clustering) ve PCA Metodolojisi:**
    Bu modül, denetimsiz makine öğrenmesi (Unsupervised Machine Learning) kullanarak oyuncuların fiziksel DNA'sını çıkarır ve benzer oyuncuları aynı kümeye atar. 

    **Süreç Nasıl İşler?**
    1. **Ölçeklendirme (Standardization):** Algoritma çalışmadan önce `Mesafe` (binlerce metre) ve `Hız` (20-30 km/h) gibi farklı birimlerdeki tüm veriler *StandardScaler* ile aynı ağırlığa (z-score) getirilir. Böylece hiçbir metrik diğerini ezmez.
    2. **K-Means Algoritması:** Sistem, veri uzayında birbirine en yakın olan oyuncuları (fiziksel olarak en çok benzeyenleri) belirlediğiniz 'Küme (Grup) Sayısına' göre otomatik olarak sınıflandırır.
    3. **Boyut İndirgeme (PCA - Principal Component Analysis):** 11 farklı atletik metrik (11 boyut) insan gözüyle anlaşılamayacağı için, yapay zeka verinin özünü (Varyansını) kaybetmeden 2 ana eksene (PCA1 ve PCA2) indirger. Haritadaki yakın noktalar, sahada aynı işi yapan oyunculardır.
    4. **Otomatik Profil İsimlendirme:** Algoritma, oluşan her bir grubun genel takım ortalamasından (Popülasyon) yüzde kaç saptığına bakar. Eğer bir grup *Sprint ve Max Hızda* ortalamanın %20 üzerindeyse, yapay zeka bu gruba otomatik olarak **"Patlayıcı Güç ve Sürat Uzmanları"** adını verir.
    """, unsafe_allow_html=True)

# ── 1. VERİ HAZIRLIĞI VE ÇEKME ───────────────────────────────────────────────
@st.cache_data(ttl=600)
def get_clustering_data():
    df = db_manager.get_all_data()
    return df

raw_data = get_clustering_data()

if raw_data.empty:
    st.warning("Yeterli veri bulunamadı. Lütfen önce sisteme veri yükleyin.")
    st.stop()

# ── FİLTRE VE HİPERPARAMETRE AYARLARI ────────────────────────────────────────
section_title("MAKİNE ÖĞRENMESİ AYARLARI", "⚙️")
st.markdown("<div style='background:#FAFAFA; padding:20px; border-radius:12px; border:1px solid #e5e7eb; margin-bottom:25px;'>", unsafe_allow_html=True)
c1, c2, c3 = st.columns([2, 1, 1])

with c1:
    available_metrics = [m for m in PRIMARY_METRICS if m in raw_data.columns]
    display_names = {m: METRICS.get(m, {}).get('display', m).upper() for m in available_metrics}
    
    selected_metrics = st.multiselect(
        "KÜMELEMEYE DAHİL EDİLECEK METRİKLER (Features)",
        options=available_metrics,
        default=available_metrics[:6] if len(available_metrics) >= 6 else available_metrics,
        format_func=lambda x: display_names.get(x, x),
        help="Algoritma oyuncuları sınıflandırırken sadece bu metrikleri dikkate alacaktır."
    )

with c2:
    num_clusters = st.slider("KÜME (PROFİL) SAYISI (k)", min_value=2, max_value=6, value=4, 
                             help="Makine öğrenmesi algoritmasının (K-Means) oyuncuları kaç farklı karakteristik profile ayıracağını seçin.")

with c3:
    min_sessions = st.number_input("MİN. SEANS (Outlier Filter)", min_value=1, value=2,
                                   help="Gürültüyü (noise) önlemek için, sadece bu sayıdan fazla seansa (idman/maç) katılmış istikrarlı oyuncular yapay zekaya dahil edilir.")
st.markdown("</div>", unsafe_allow_html=True)

if len(selected_metrics) < 2:
    st.error("Kümeleme analizi yapabilmek için en az 2 adet karakteristik metrik seçmelisiniz.")
    st.stop()

# ── VERİ ÖN İŞLEME (DATA PREPROCESSING) ───────────────────────────────────────
# Oyuncu bazında genel aritmetik ortalamaları al
player_stats = raw_data.groupby(['player_name', 'age_group']).agg(
    seans_sayisi=('tarih', 'count'),
    **{m: (m, 'mean') for m in selected_metrics}
).reset_index()

# Gürültü (Noise) Filtreleme ve Temizlik
player_stats = player_stats[player_stats['seans_sayisi'] >= min_sessions].copy()
player_stats = player_stats.dropna(subset=selected_metrics)

if len(player_stats) < num_clusters:
    st.warning(f"Kriterleri karşılayan yeterli oyuncu yok ({len(player_stats)} oyuncu bulundu). Lütfen seans filtresini düşürün veya küme sayısını azaltın.")
    st.stop()

# ── 2. YAPAY ZEKA (K-MEANS CLUSTERING & PCA) ──────────────────────────────────
features = player_stats[selected_metrics]
scaler = StandardScaler()
scaled_features = scaler.fit_transform(features) # Veriler aynı ağırlığa getiriliyor

# K-Means Kümeleme Motoru
kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init='auto')
clusters = kmeans.fit_predict(scaled_features)
player_stats['Raw_Grup'] = [f"Profil {c+1}" for c in clusters]

# PCA Boyut İndirgeme (2D Görselleştirme için)
pca = PCA(n_components=2)
pca_components = pca.fit_transform(scaled_features)
player_stats['PCA1'] = pca_components[:, 0]
player_stats['PCA2'] = pca_components[:, 1]

# ── 3. AKILLI PROFİLLEME VE İSİMLENDİRME MOTORU (SMART LABELING) ─────────────
# AÇIKLAMA: Sistem, oluşan kümelerin özelliklerini analiz eder ve onlara "Profil 1" gibi 
# ruhsuz isimler vermek yerine, spor bilimi literatürüne uygun akıllı etiketler atar.
global_means = player_stats[selected_metrics].mean()
cluster_means = player_stats.groupby('Raw_Grup')[selected_metrics].mean().reset_index()

cluster_profiles = {}
for i in range(num_clusters):
    c_name = f"Profil {i+1}"
    c_data = cluster_means[cluster_means['Raw_Grup'] == c_name].iloc[0][selected_metrics]
    
    # Genel popülasyon ortalamasına göre yüzde kaç saptılar? (Varyans Tespiti)
    diffs = ((c_data - global_means) / global_means.replace(0, 0.1)) * 100
    sorted_diffs = diffs.sort_values(ascending=False)
    
    # Kümenin adını, en yüksek sapan (en baskın) özelliğe göre belirle
    best_metric = sorted_diffs.index[0]
    worst_metric = sorted_diffs.index[-1]
    
    # Sınıflandırma Kuralları (Fiziksel Tipoloji Algoritması)
    if sorted_diffs.iloc[0] > 6: # Eğer bir metrikte %6'dan fazla elit bir sapma varsa
        if any(term in best_metric.lower() for term in ['speed', 'smax', 'dist_25']):
            desc = "🏃 Patlayıcı Güç ve Sürat Uzmanları"
        elif any(term in best_metric.lower() for term in ['distance', 'metrage', 'amp']):
            desc = "🔋 Yüksek Motor Kapasite ve Dayanıklılık"
        elif any(term in best_metric.lower() for term in ['load', 'acc', 'dec']):
            desc = "🏋️ Yüksek Yoğunluklu Mekanik Yüklenenler"
        else:
            desc = f"⭐ {display_names.get(best_metric, best_metric)} Uzmanları"
            
    elif sorted_diffs.iloc[-1] < -10 and sorted_diffs.iloc[0] < 2: 
        # Her parametrede eksik kalmışlarsa (Hem zirveleri yok, hem dipleri çok düşük)
        desc = "📉 Gelişim Bölgesi (Fiziksel Yükleme Gerektirenler)"
    else:
        desc = "⚖️ Dengeli / Görev Adamı (Sıfır Sapma)"
        
    cluster_profiles[c_name] = {
        'desc': desc,
        'diffs': diffs,
        'full_name': f"Grup {i+1}: {desc}" # Yeni Akıllı İsim
    }

# Akıllı isimleri ana veriye işle
player_stats['Akilli_Grup'] = player_stats['Raw_Grup'].map(lambda x: cluster_profiles[x]['full_name'])

st.divider()

# ── 4. GÖRSELLEŞTİRME (DAĞILIM HARİTASI VE KÜMELER) ───────────────────────────
section_title("OYUNCU PROFİLİ DAĞILIM HARİTASI (PCA PROJECTION)", "🌌", 
              "Yapay zeka, oyuncuları 11 boyutlu özellik vektöründen 2 boyuta indirgeyerek haritalandırmıştır. Birbirine yakın noktalar, fiziksel DNA'sı aynı olan oyunculardır.")

hover_data = {'PCA1': False, 'PCA2': False, 'age_group': True}
for m in selected_metrics: hover_data[m] = ':.1f'

cluster_colors = [COLORS['RED'], '#1F2937', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6']

fig_scatter = px.scatter(
    player_stats, x='PCA1', y='PCA2', color='Akilli_Grup',
    hover_name='player_name', hover_data=hover_data,
    color_discrete_sequence=cluster_colors,
    labels={'age_group': 'Yaş Grubu', 'Akilli_Grup': 'Fiziksel Tipoloji (Küme)'}
)

fig_scatter.update_traces(marker=dict(size=12, line=dict(width=1.5, color='white')), opacity=0.85)
fig_scatter.update_layout(
    margin=dict(l=20, r=20, t=20, b=20), height=550,
    plot_bgcolor='#FAFAFA', paper_bgcolor='white',
    legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02, title_text="<b>KÜMELER (CLUSTERS)</b>"),
    xaxis=dict(title="Temel Bileşen 1 (PCA1 Vektörü)", showgrid=True, gridcolor='#E5E7EB', zeroline=True, zerolinecolor='#9CA3AF'),
    yaxis=dict(title="Temel Bileşen 2 (PCA2 Vektörü)", showgrid=True, gridcolor='#E5E7EB', zeroline=True, zerolinecolor='#9CA3AF')
)

st.plotly_chart(fig_scatter, width='stretch')

# ── 5. GRUP ÖZELLİKLERİ VE AĞIRLIKLARI (DETAYLI ANALİZ) ──────────────────────
section_title("KÜMELERİN KARAKTERİSTİK ÖZELLİKLERİ VE SAPMA ORANLARI", "📊", 
              "Sistemin bu grubu neden oluşturduğunu, grubun takım ortalamasından (medyan) yüzde kaç saptığını gösterir.")

cols = st.columns(num_clusters)
for i in range(num_clusters):
    raw_name = f"Profil {i+1}"
    profile_info = cluster_profiles[raw_name]
    c_data = cluster_means[cluster_means['Raw_Grup'] == raw_name]
    player_count = len(player_stats[player_stats['Raw_Grup'] == raw_name])
    color = cluster_colors[i % len(cluster_colors)]
    
    with cols[i]:
        st.markdown(f"""
        <div style="background:white; border:1px solid {COLORS['GRAY_200']}; border-top:6px solid {color}; 
                    border-radius:12px; padding:20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); height:100%;">
            <div style="font-family:'Bebas Neue',sans-serif; font-size:22px; color:{COLORS['GRAY_800']}; line-height:1.1;">
                {profile_info['desc']}
            </div>
            <div style="font-size:11px; color:{COLORS['GRAY_500']}; font-weight:700; margin-bottom:15px; margin-top:6px; letter-spacing:0.5px;">
                👥 GRUP HACMİ: {player_count} OYUNCU
            </div>
        """, unsafe_allow_html=True)
        
        for m in selected_metrics:
            val = c_data[m].values[0]
            diff = profile_info['diffs'][m]
            unit = METRICS.get(m, {}).get('unit', '')
            m_display = display_names.get(m, m)
            
            # Farkı (Varyansı) görselleştiren renkli göstergeler
            if diff > 3:
                diff_html = f"<span style='color:#10B981; font-weight:800; font-size:11px;'>▲ +{diff:.1f}% (Elit)</span>"
            elif diff < -3:
                diff_html = f"<span style='color:#EF4444; font-weight:800; font-size:11px;'>▼ {diff:.1f}% (Zayıf)</span>"
            else:
                diff_html = f"<span style='color:{COLORS['GRAY_400']}; font-weight:700; font-size:11px;'>▬ {diff:.1f}% (Ort.)</span>"

            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px dashed {COLORS['GRAY_100']}; padding:8px 0;">
                <span style="font-size:11px; color:{COLORS['GRAY_700']}; font-weight:700;">{m_display}</span>
                <div style="text-align:right;">
                    <div style="font-size:14px; color:{COLORS['GRAY_900']}; font-weight:900;">{val:.1f} <span style="font-size:9px;color:{COLORS['GRAY_400']};">{unit}</span></div>
                    {diff_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# ── 6. AÇIKLAMALI OYUNCU LİSTELERİ VE DIŞA AKTARIM ───────────────────────────
section_title("KADRO MÜHENDİSLİĞİ: PROFİLLERE GÖRE OYUNCU DAĞILIMI", "📋", 
              "Hangi oyuncunun yapay zeka tarafından hangi karakteristik gruba dahil edildiğini gösteren operasyonel tam liste.")

display_df = player_stats[['player_name', 'age_group', 'Akilli_Grup'] + selected_metrics].copy()
display_df.columns = ['OYUNCU ADI', 'YAŞ GRUBU', 'ATLETİK PROFİL (KÜME)'] + [display_names.get(m, m) for m in selected_metrics]

# Kümeye ve sonra oyuncu adına göre alfabetik sırala (Hiyerarşik Düzen)
display_df = display_df.sort_values(['ATLETİK PROFİL (KÜME)', 'OYUNCU ADI']).reset_index(drop=True)

st.dataframe(display_df, width='stretch', hide_index=True)

st.markdown('<div class="tff-footer"><p>Rugby Performans Sistemi · Yapay Zeka ve İstatistik Departmanı</p></div>', unsafe_allow_html=True)