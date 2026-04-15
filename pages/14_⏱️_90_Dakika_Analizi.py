import streamlit as st
import pandas as pd
import numpy as np
from database import db_manager
from styles import inject_styles, page_header, section_title, COLORS, info_box
from utils import render_export_buttons
import plotly.express as px
import plotly.graph_objects as go
from config import METRICS

st.set_page_config(page_title="Verimlilik ve Yoğunluk Analizi | TFF", layout="wide")
inject_styles()

page_header("⏱️", "ATLETİK YOĞUNLUK VE VERİMLİLİK", "Per 90 ve m/min (Birim Dakika) bazlı iş yükü analiz laboratuvarı.")

# 📝 BİLGİLENDİRME KUTUSU (Metodoloji)
info_box("""
<b>YOĞUNLUK (INTENSITY) ANALİZİ NEDİR?</b><br>
Farklı süreler sahada kalan oyuncuları (Örn: 90 dk oynayan stoper vs 30 dk oynayan forvet) adil bir şekilde kıyaslamak için kümülatif veriler (hacim), sahada kalınan dakikaya oranlanır. 
Bu analiz bize <b>"En çok koşan"</b> oyuncuyu değil, <b>"Sahada kaldığı süre boyunca en yoğun/şiddetli eforu sarf eden"</b> oyuncuyu bulmamızı sağlar.
""")

# ── 1. VERİ HAZIRLIĞI VE FİLTRELEME ───────────────────────────────────────────
c1, c2, c3 = st.columns(3)
with c1:
    age_group = st.selectbox("YAŞ GRUBU", ["_", "U19", "U18", "U17", "6", "U15"], key="p90_age")
    
raw_data = db_manager.get_data_by_age_group(age_group)

if raw_data.empty:
    st.warning(f"{age_group} grubu için analiz edilecek veri bulunamadı.")
    st.stop()

camps_df = db_manager.get_camps(age_group)
camp_options = {row['camp_name']: row['camp_id'] for _, row in camps_df.iterrows()}

with c2:
    if camp_options:
        sel_camp_label = st.selectbox("KAMP SEÇİMİ", list(camp_options.keys()), key="p90_camp")
        sel_camp_id = camp_options[sel_camp_label]
    else:
        st.warning("Kamp bulunamadı.")
        st.stop()

with c3:
    # Çok düşük süreli veriler 'Per 90' analizini patlatır (Örn: 1 dk oynayıp 1 sprint atanı 90 sprint atacak sanır)
    min_minutes = st.number_input("MİN. DAKİKA FİLTRESİ (Outlier Koruması)", min_value=5, value=30, step=5, 
                                  help="İstatistiksel sapmayı önlemek için bu sürenin altında sahada kalanlar analize dahil edilmez.")

# Kamp verisini filtrele
camp_raw = raw_data[(raw_data['camp_id'] == sel_camp_id) & (raw_data['minutes'] >= min_minutes)].copy()

if camp_raw.empty:
    st.warning("Seçilen dakika filtresine uygun kamp verisi bulunamadı.")
    st.stop()

# ── 2. METRİK TANIMLAMALARI VE DİNAMİK NORMALİZASYON (HATA ÇÖZÜMÜ) ─────────────
# AÇIKLAMA: Anlık veriler (SMax, Kalp Atışı vb.) dakikaya oranlanamaz. Sadece kümülatifler oranlanır.
accumulative_metrics = ['total_distance', 'dist_25_plus', 'player_load', 'metrage', 'amp', 'acc_3_plus', 'dec_3_minus', 'hsr_dist']
valid_metrics = [m for m in accumulative_metrics if m in camp_raw.columns and camp_raw[m].notna().any()]

if not valid_metrics:
    st.error("Veritabanında 'Per Minute' hesaplamasına uygun kümülatif veri bulunamadı.")
    st.stop()

# GÜVENLİ HESAPLAMA MOTORU (Önceki hatayı çözen kısım)
p90_df = camp_raw.copy()
for m in valid_metrics:
    # 1. m/min (Birim Dakika - Antrenman Şiddeti)
    p90_df[f"{m}_pm"] = np.where(p90_df['minutes'] > 0, p90_df[m] / p90_df['minutes'], 0)
    # 2. P90 (90 Dakika Projeksiyonu - Maç Şiddeti)
    p90_df[f"{m}_p90"] = p90_df[f"{m}_pm"] * 90

# Dinamik Referans Metrik (total_distance yoksa eldeki ilk metriği kullan)
ref_metric = 'total_distance' if 'total_distance' in valid_metrics else valid_metrics[0]
ref_pm = f"{ref_metric}_pm"

# AEI (Athletic Efficiency Index) Hesabı - Güvenli Kontrol
has_aei = False
if 'total_distance' in valid_metrics and 'player_load' in valid_metrics:
    p90_df['efficiency_index'] = p90_df['total_distance'] / p90_df['player_load'].replace(0, np.nan)
    has_aei = True

# ── 3. HİYERARŞİK LİDERLİK KARTLARI (KAMP ÖZETİ) ─────────────────────────────
st.markdown("### 🏆 KAMP YOĞUNLUK VE VERİMLİLİK HİYERARŞİSİ")
h_cols = st.columns(3)

# 1. Günün Parlaması: Kampın en şiddetli tek seansı (Birim dakika bazında)
best_session = p90_df.sort_values(ref_pm, ascending=False).iloc[0]
ref_unit = METRICS.get(ref_metric, {}).get('unit', '')
ref_display = METRICS.get(ref_metric, {}).get('display', ref_metric).upper()

with h_cols[0]:
    st.markdown(f"""
    <div style='background:white; padding:20px; border-radius:15px; border-top:5px solid {COLORS['GREEN']}; box-shadow: 0 4px 6px rgba(0,0,0,0.05); height: 100%;'>
        <div style='font-size:12px; color:#6B7280; font-weight:bold;'>⚡ ANLIK PATLAMA (ZİRVE SEANS)</div>
        <div style='font-family:Bebas Neue; font-size:26px; margin-top:5px; color:{COLORS['GRAY_900']};'>{best_session['player_name'].upper()}</div>
        <div style='font-size:16px; color:{COLORS['GREEN']}; font-weight:bold;'>{best_session[ref_pm]:.1f} {ref_unit}/min <span style='font-size:12px; color:#9CA3AF; font-weight:normal;'>(Şiddet)</span></div>
        <div style='font-size:11px; color:#9CA3AF; margin-top:5px;'>Tarih: {best_session['tarih'].strftime('%d.%m.%Y')} ({best_session['tip']})</div>
    </div>
    """, unsafe_allow_html=True)

# 2. Kampın En Yüksek Kapasitesi (Kamp boyu ortalama şiddeti en yüksek olan)
avg_intensity = p90_df.groupby('player_name')[ref_pm].mean()
top_engine_name = avg_intensity.idxmax()
top_engine_val = avg_intensity.max()

with h_cols[1]:
    st.markdown(f"""
    <div style='background:white; padding:20px; border-radius:15px; border-top:5px solid {COLORS['BLACK']}; box-shadow: 0 4px 6px rgba(0,0,0,0.05); height: 100%;'>
        <div style='font-size:12px; color:#6B7280; font-weight:bold;'>🔋 KAMPIN MOTORU (EN YÜKSEK ORTALAMA)</div>
        <div style='font-family:Bebas Neue; font-size:26px; margin-top:5px; color:{COLORS['GRAY_900']};'>{top_engine_name.upper()}</div>
        <div style='font-size:16px; color:{COLORS['BLACK']}; font-weight:bold;'>{top_engine_val:.1f} {ref_unit}/min <span style='font-size:12px; color:#9CA3AF; font-weight:normal;'>(Kamp Ort.)</span></div>
        <div style='font-size:11px; color:#9CA3AF; margin-top:5px;'>Oynadığı her dakika için ortalama {ref_display}.</div>
    </div>
    """, unsafe_allow_html=True)

# 3. AEI (Athletic Efficiency Index) - Mekanik Yük vs Mesafe Verimliliği
with h_cols[2]:
    if has_aei:
        avg_efficiency = p90_df.groupby('player_name')['efficiency_index'].mean()
        top_efficient = avg_efficiency.idxmax()
        top_efficient_val = avg_efficiency.max()
        st.markdown(f"""
        <div style='background:white; padding:20px; border-radius:15px; border-top:5px solid #10B981; box-shadow: 0 4px 6px rgba(0,0,0,0.05); height: 100%;'>
            <div style='font-size:12px; color:#6B7280; font-weight:bold;'>💎 EKONOMİK ATLET (MAX VERİMLİLİK)</div>
            <div style='font-family:Bebas Neue; font-size:26px; margin-top:5px; color:{COLORS['GRAY_900']};'>{top_efficient.upper()}</div>
            <div style='font-size:16px; color:#10B981; font-weight:bold;'>{top_efficient_val:.1f} Katsayı <span style='font-size:12px; color:#9CA3AF; font-weight:normal;'>(AEI)</span></div>
            <div style='font-size:11px; color:#9CA3AF; margin-top:5px;'>1 Birim Player Load başına gidilen metre.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style='background:white; padding:20px; border-radius:15px; border-top:5px solid {COLORS['GRAY_400']}; box-shadow: 0 4px 6px rgba(0,0,0,0.05); height: 100%;'>
            <div style='font-size:12px; color:#6B7280; font-weight:bold;'>💎 EKONOMİK ATLET</div>
            <div style='font-family:Bebas Neue; font-size:20px; margin-top:5px; color:{COLORS['GRAY_500']};'>VERİ YETERSİZ</div>
            <div style='font-size:11px; color:#9CA3AF; margin-top:5px;'>Hesaplama için Player Load ve Mesafe verisi gereklidir.</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ── 4. ANALİZ SEKMELERİ ───────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Şiddet Tablosu (m/min & P90)", "📈 Verimlilik Analizi (AEI Çeyreklikleri)", "⚖️ Karşılaştırmalı Yoğunluk Grafiği"])

with tab1:
    section_title("KAMP BOYU DAKİKA BAŞINA ÜRETİM TABLOSU", "📏")
    st.markdown("<div style='font-size:13px; color:gray; margin-bottom:15px;'>M/min sütunları oyuncunun sahada kaldığı sürede dakikada ne kadar üretim yaptığını, P90 sütunları ise bu tempoyu 90 dakikaya yaysaydı oluşacak varsayımsal rakamları gösterir.</div>", unsafe_allow_html=True)
    
    # Görüntülenecek metrikleri seçtirelim ki tablo kalabalık olmasın
    default_disp = [m for m in ['total_distance', 'dist_25_plus', 'player_load'] if m in valid_metrics]
    if not default_disp: default_disp = valid_metrics[:3]
    
    disp_m = st.multiselect("TABLODA GÖSTERİLECEK METRİKLER", valid_metrics, default=default_disp, format_func=lambda x: METRICS.get(x, {}).get('display', x).upper())
    
    if disp_m:
        # Tablo için Dataframe hazırlığı (Ortalamalar alınır)
        agg_dict = {'minutes': 'sum', 'tarih': 'count'}
        for m in disp_m:
            agg_dict[f"{m}_pm"] = 'mean'
            agg_dict[f"{m}_p90"] = 'mean'
            
        view_df = p90_df.groupby('player_name').agg(agg_dict).reset_index()
        view_df = view_df.rename(columns={'minutes': 'TOPLAM SÜRE (Dk)', 'tarih': 'SEANS'})
        
        # Dinamik kolon isimleri
        for m in disp_m:
            disp_name = METRICS.get(m, {}).get('display', m).upper()
            view_df = view_df.rename(columns={f"{m}_pm": f"ORT. {disp_name} (/min)", f"{m}_p90": f"PROJEKSİYON: {disp_name} (P90)"})
        
        st.dataframe(view_df.style.format(precision=1).background_gradient(cmap='Reds', subset=[c for c in view_df.columns if '(/min)' in c]), width='stretch', hide_index=True)
        render_export_buttons(df=view_df, key_prefix="p90_table", filename=f"yogunluk_analizi_{sel_camp_label}")
    else:
        st.info("Tablo oluşturmak için en az bir metrik seçin.")

with tab2:
    section_title("AEI: ATLETİK VERİMLİLİK İNDEKSİ", "⚖️")
    st.info("AEI (Athletic Efficiency Index): Oyuncunun ürettiği toplam mesafeyi, vücuduna binen mekanik yüke (Player Load) böler. Yüksek olanlar verimli koşan/enerji saklayan elit oyunculardır.")
    
    if has_aei:
        # Oyuncu bazlı ortalama AEI hesabı
        aei_df = p90_df.groupby('player_name').agg(
            avg_dist=('total_distance_p90', 'mean'),
            avg_load=('player_load_p90', 'mean'),
            avg_aei=('efficiency_index', 'mean')
        ).reset_index()
        
        fig_aei = px.scatter(aei_df, x='avg_load', y='avg_dist', 
                             color='avg_aei', color_continuous_scale='RdYlGn',
                             size='avg_aei', hover_name='player_name', text='player_name',
                             labels={'avg_load': 'Ortalama P90 Player Load (Zorlanma)', 
                                     'avg_dist': 'Ortalama P90 Mesafe (Üretim)',
                                     'avg_aei': 'Verimlilik Skoru'})
        
        fig_aei.update_traces(textposition='top center', textfont=dict(size=10, weight='bold'))
        fig_aei.update_layout(template="plotly_white", height=600, title="<b>Mekanik Yük vs Mesafe Üretimi (Quadrant)</b>",
                              shapes=[
                                  dict(type='line', yref='y', y0=aei_df['avg_dist'].mean(), y1=aei_df['avg_dist'].mean(), xref='paper', x0=0, x1=1, line=dict(color='gray', dash='dash')),
                                  dict(type='line', xref='x', x0=aei_df['avg_load'].mean(), x1=aei_df['avg_load'].mean(), yref='paper', y0=0, y1=1, line=dict(color='gray', dash='dash'))
                              ])
        
        # Bölgelere Metin Ekleme
        fig_aei.add_annotation(x=aei_df['avg_load'].max(), y=aei_df['avg_dist'].max(), text="Çok Çalışanlar", showarrow=False, xanchor="right")
        fig_aei.add_annotation(x=aei_df['avg_load'].min(), y=aei_df['avg_dist'].max(), text="🌟 Ekonomik/Elit", showarrow=False, xanchor="left", font=dict(color=COLORS['SUCCESS']))
        fig_aei.add_annotation(x=aei_df['avg_load'].max(), y=aei_df['avg_dist'].min(), text="⚠️ Verimsiz Zorlanma", showarrow=False, xanchor="right", font=dict(color=COLORS['DANGER']))
        
        st.plotly_chart(fig_aei, width='stretch')
    else:
        st.warning("Verimlilik hesabı (AEI) için 'Total Distance' ve 'Player Load' metrikleri veri setinde bulunmalıdır.")

with tab3:
    section_title("GÜNLÜK YOĞUNLUK DEĞİŞİMİ (BAR CHART)", "📊")
    st.markdown("Seçilen yoğunluk metriğinin kamp boyunca gün gün nasıl değiştiğini inceleyin.")
    
    bar_m = st.selectbox("Grafik Metriği (m/min bazında)", valid_metrics, format_func=lambda x: METRICS.get(x, {}).get('display', x).upper(), key="p90_barm")
    target_p = st.multiselect("İncelenecek Oyuncular", sorted(p90_df['player_name'].unique()), default=sorted(p90_df['player_name'].unique())[:3])
    
    if target_p:
        plot_data = p90_df[p90_df['player_name'].isin(target_p)].copy()
        plot_data['tarih_str'] = plot_data['tarih'].dt.strftime('%d.%m')
        
        fig_bar = px.bar(plot_data, x='tarih_str', y=f"{bar_m}_pm", color='player_name', barmode='group',
                         labels={'tarih_str': 'Tarih', f"{bar_m}_pm": f"Şiddet İndeksi ({METRICS.get(bar_m, {}).get('unit', '')}/min)", 'player_name': 'Oyuncu'})
        fig_bar.update_layout(template="plotly_white", height=500, title=f"<b>Birim Dakika Performans Değişimi</b>")
        st.plotly_chart(fig_bar, width='stretch')

# ── BİLGİ VE METODOLOJİ ───────────────────────────────────────────────────────
st.divider()
with st.expander("🔬 'PER 90' VE VERİMLİLİK HESABI NASIL YAPILIR? (TEKNİK DETAYLAR)", expanded=False):
    st.markdown("""
    ### 1. Neden Şiddet (Intensity) Ölçüyoruz?
    Bir antrenmanda 6.000 metre koşan bir stoper ile 4.000 metre koşan bir kanat oyuncusunu ham rakamlarla kıyaslamak hatadır. Eğer stoper bunu 90 dakikada, kanat oyuncusu 30 dakikada yaptıysa; kanat oyuncusunun **antrenman şiddeti (m/min)** çok daha yüksektir.
    Bu analiz, "Hacmi" (Volume) aradan çıkartarak tüm oyuncuları aynı teraziye koyar.
    
    ### 2. Hesaplanan İndeksler:
    * **Birim Dakika (m/min):** `Ham Kümülatif Veri / Oynanan Dakika`. Oyuncunun sahada kaldığı her bir dakika için ürettiği iş. (Avrupa kulüplerinin antrenman planlamasında kullandığı temel metrik).
    * **P90 (90 Dakika Projeksiyonu):** `(m/min) * 90`. Oyuncu bu şiddette 90 dakika oynasaydı üreteceği varsayımsal rakam.
    * **AEI (Athletic Efficiency Index):** `Toplam Mesafe / Player Load`. Vücudun maruz kaldığı her 1 birimlik sarsıntıya/yüke karşılık kaç metre ilerlendiğini ölçer. Zayıf koşu mekaniği olan veya aşırı yorgun oyuncuların AEI puanı düşüktür (Boşa enerji harcarlar).
    """)

st.markdown('<div class="tff-footer"><p>Rugby Performans Sistemi · Performans Analiz Laboratuvarı</p></div>', unsafe_allow_html=True)