import streamlit as st
import pandas as pd
import plotly.express as px
from config import AGE_GROUPS, METRICS, PRIMARY_METRICS, DEFAULT_MINUTES
from database import db_manager
from styles import inject_styles, page_header, section_title, info_box, COLORS

st.set_page_config(page_title="İstatistikler & Trendler | TFF", layout="wide")
inject_styles()

page_header("📈", "İSTATİSTİKLER VE KAMP RAPORU", "Tanımlayıcı istatistikler, kamp bazlı özetler, varyans ve trend analizleri")

# ── Üst Filtreler ─────────────────────────────────────────────────────────────
c1, c2 = st.columns([1, 3])
with c1:
    age_group = st.selectbox("YAŞ GRUBU SEÇİN", AGE_GROUPS, key="stat_age")

# Veriyi Çek
raw_df = db_manager.get_data_by_age_group(age_group)

if raw_df.empty:
    st.warning(f"{age_group} için veritabanında henüz veri bulunmuyor.")
    st.stop()

# ── Dakika Filtreleri (Veri Kirliliğini Önler) ───────────────────────────────
with st.expander("⚙️ DAKİKA VE VERİ FİLTRELERİ", expanded=False):
    st.markdown("<div style='font-size:13px; color:#6B7280; margin-bottom:10px;'>İstatistiksel sapmaları (Outliers) önlemek için kısa süreli katılımları devre dışı bırakın.</div>", unsafe_allow_html=True)
    dk1, dk2 = st.columns(2)
    with dk1: min_train_dk = st.number_input("Minimum Antrenman Dakikası", value=DEFAULT_MINUTES['TRAINING'], step=5, key="st_dk_tr")
    with dk2: min_match_dk = st.number_input("Minimum Maç Dakikası", value=DEFAULT_MINUTES['MATCH'], step=5, key="st_dk_ma")

def apply_minute_filter(data):
    if data.empty: return data
    is_tr = data['tip'].str.upper().str.contains('TRAINING')
    is_ma = data['tip'].str.upper().str.contains('MATCH')
    mask = (is_tr & (data['minutes'] >= min_train_dk)) | (is_ma & (data['minutes'] >= min_match_dk))
    return data[mask].copy()

df = apply_minute_filter(raw_df)

if df.empty:
    st.warning("Filtre sonrası incelenecek veri kalmadı.")
    st.stop()

# Kamp İsimlerini Merge Et
camps_df = db_manager.get_camps(age_group)
if not camps_df.empty:
    df = df.merge(camps_df[['camp_id', 'camp_name']], on='camp_id', how='left')
else:
    df['camp_name'] = "Kamp " + df['camp_id'].astype(str)

# Sayısal Metrik Listesini Hazırla
numeric_cols = [c for c in PRIMARY_METRICS if c in df.columns and df[c].notna().any()]

# ── TAB YAPISI ────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "📋 KAMP RAPORU (ÖZET İSTATİSTİKLER)", 
    "📊 DAĞILIM (KUTU GRAFİĞİ)", 
    "📉 KORELASYON MATRİSİ", 
    "📈 ZAMAN SERİSİ (TREND)"
])

# ── TAB 1: KAMP RAPORU VE TANIMLAYICI İSTATİSTİKLER (YENİ EKLENEN KISIM) ──────
with tabs[0]:
    section_title("KAMP GENEL RAPORU VE KATILIM ANALİZİ", "📋")
    info_box("Bu bölüm, seçilen kampın genel profilini, oyuncu katılım istatistiklerini ve seanslar arası performans/standart sapma farklılıklarını raporlar.")
    
    rep_camp = st.selectbox("RAPORLANACAK KAMPI SEÇİN", sorted(df['camp_name'].dropna().unique()), key="rep_camp")
    cdf = df[df['camp_name'] == rep_camp].copy()
    
    if not cdf.empty:
        # Temel İstatistikler
        total_days = cdf['tarih'].nunique()
        match_days = cdf[cdf['tip'].str.upper().str.contains('MATCH')]['tarih'].nunique()
        train_days = cdf[cdf['tip'].str.upper().str.contains('TRAINING')]['tarih'].nunique()
        total_players = cdf['player_name'].nunique()
        
        # Katılım Analizi (Attendance)
        attendance = cdf.groupby('player_name')['tarih'].nunique()
        max_att_val = attendance.max()
        min_att_val = attendance.min()
        
        most_att_players = attendance[attendance == max_att_val].index.tolist()
        least_att_players = attendance[attendance == min_att_val].index.tolist()
        
        # KPI Kartları
        st.markdown("<h4 style='font-family: DM Sans; color: #374151; font-size: 16px;'>1. KAMP HACMİ VE KATILIM PROFİLİ</h4>", unsafe_allow_html=True)
        k1, k2, k3, k4 = st.columns(4)
        with k1: st.markdown(f"<div class='metric-card' style='padding:15px;'><div class='sc-label'>TOPLAM OYUNCU</div><div class='sc-val' style='font-size:26px;'>{total_players}</div></div>", unsafe_allow_html=True)
        with k2: st.markdown(f"<div class='metric-card' style='padding:15px;'><div class='sc-label'>GEÇERLİ GÜN / SEANS</div><div class='sc-val' style='font-size:26px;'>{total_days}</div></div>", unsafe_allow_html=True)
        with k3: st.markdown(f"<div class='metric-card' style='padding:15px;'><div class='sc-label'>ANTRENMAN GÜNÜ</div><div class='sc-val' style='font-size:26px; color:{COLORS['BLACK']};'>{train_days}</div></div>", unsafe_allow_html=True)
        with k4: st.markdown(f"<div class='metric-card' style='padding:15px;'><div class='sc-label'>MAÇ GÜNÜ</div><div class='sc-val' style='font-size:26px; color:{COLORS['RED']};'>{match_days}</div></div>", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background-color: #F9FAFB; padding: 15px; border-radius: 8px; border-left: 4px solid {COLORS['SUCCESS']}; margin-top:10px;">
            <b style="color: #374151;">🏅 En İstikrarlı Oyuncular ({max_att_val} Seans):</b> <span style="color: #4B5563;">{', '.join(most_att_players[:10])} {', ...' if len(most_att_players)>10 else ''}</span>
        </div>
        <div style="background-color: #FEF2F2; padding: 15px; border-radius: 8px; border-left: 4px solid {COLORS['DANGER']}; margin-top:10px;">
            <b style="color: #991B1B;">⚠️ En Az Seans Görenler ({min_att_val} Seans):</b> <span style="color: #B91C1C;">{', '.join(least_att_players[:10])} {', ...' if len(least_att_players)>10 else ''}</span>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Detaylı Günlük Varyasyon ve Tanımlayıcı İstatistikler
        st.markdown("<h4 style='font-family: DM Sans; color: #374151; font-size: 16px;'>2. METRİK BAZLI GÜNLÜK VARYANS ANALİZİ (EXTREMES)</h4>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 13px; color: #6B7280; margin-bottom: 15px;'>Hangi gün takım en çok zorlandı? Hangi gün performans dağılımı (Standart Sapma) en eşitsizdi? İncelemek istediğiniz metriği seçin.</div>", unsafe_allow_html=True)
        
        stat_metric = st.selectbox("Analiz Edilecek Metrik Seçin:", numeric_cols, format_func=lambda x: METRICS.get(x, {}).get('display', x).upper(), key="stat_m")
        
        if stat_metric:
            # Günlük ortalama ve standart sapmaları hesapla
            daily_stats = cdf.groupby(['tarih', 'tip'])[stat_metric].agg(['mean', 'std', 'count']).dropna().reset_index()
            daily_stats['tarih_str'] = daily_stats['tarih'].dt.strftime('%d.%m.%Y')
            
            if not daily_stats.empty and len(daily_stats) > 1:
                # Max ve Min Mean
                idx_max_mean = daily_stats['mean'].idxmax()
                idx_min_mean = daily_stats['mean'].idxmin()
                
                # Max ve Min STD
                idx_max_std = daily_stats['std'].idxmax()
                idx_min_std = daily_stats['std'].idxmin()

                m_unit = METRICS.get(stat_metric, {}).get('unit', '')

                # 4'lü Rapor Kartı
                c_sd1, c_sd2 = st.columns(2)
                with c_sd1:
                    st.markdown(f"""
                    <div style="border: 1px solid #E5E7EB; border-radius: 8px; padding: 15px; margin-bottom:10px;">
                        <div style="font-size: 11px; font-weight: bold; color: #6B7280; text-transform: uppercase;">🔥 Takım Ortalamasının En Yüksek Olduğu Gün</div>
                        <div style="font-size: 20px; font-weight: bold; color: {COLORS['GRAY_900']}; margin-top: 5px;">{daily_stats.loc[idx_max_mean, 'tarih_str']} ({daily_stats.loc[idx_max_mean, 'tip']})</div>
                        <div style="font-size: 18px; color: {COLORS['RED']}; font-weight: bold;">{daily_stats.loc[idx_max_mean, 'mean']:.1f} <span style="font-size:12px; color:#9CA3AF;">{m_unit}</span></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div style="border: 1px solid #E5E7EB; border-radius: 8px; padding: 15px;">
                        <div style="font-size: 11px; font-weight: bold; color: #6B7280; text-transform: uppercase;">📉 Takım Ortalamasının En Düşük Olduğu Gün</div>
                        <div style="font-size: 20px; font-weight: bold; color: {COLORS['GRAY_900']}; margin-top: 5px;">{daily_stats.loc[idx_min_mean, 'tarih_str']} ({daily_stats.loc[idx_min_mean, 'tip']})</div>
                        <div style="font-size: 18px; color: #3B82F6; font-weight: bold;">{daily_stats.loc[idx_min_mean, 'mean']:.1f} <span style="font-size:12px; color:#9CA3AF;">{m_unit}</span></div>
                    </div>
                    """, unsafe_allow_html=True)

                with c_sd2:
                    st.markdown(f"""
                    <div style="border: 1px solid #E5E7EB; border-radius: 8px; padding: 15px; margin-bottom:10px;">
                        <div style="font-size: 11px; font-weight: bold; color: #6B7280; text-transform: uppercase;">⚠️ En Heterojen Gün (Max Standart Sapma)</div>
                        <div style="font-size: 12px; color: #9CA3AF; margin-bottom: 5px;">Takım içi yük dağılımının en dengesiz/eşitsiz olduğu gün.</div>
                        <div style="font-size: 18px; font-weight: bold; color: {COLORS['GRAY_900']};">{daily_stats.loc[idx_max_std, 'tarih_str']} <span style="font-size:14px; font-weight:normal;">(Sapma: ±{daily_stats.loc[idx_max_std, 'std']:.1f})</span></div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"""
                    <div style="border: 1px solid #E5E7EB; border-radius: 8px; padding: 15px;">
                        <div style="font-size: 11px; font-weight: bold; color: #6B7280; text-transform: uppercase;">🎯 En Homojen Gün (Min Standart Sapma)</div>
                        <div style="font-size: 12px; color: #9CA3AF; margin-bottom: 5px;">Tüm oyuncuların birbirine en yakın performansı sergilediği gün.</div>
                        <div style="font-size: 18px; font-weight: bold; color: {COLORS['GRAY_900']};">{daily_stats.loc[idx_min_std, 'tarih_str']} <span style="font-size:14px; font-weight:normal;">(Sapma: ±{daily_stats.loc[idx_min_std, 'std']:.1f})</span></div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Varyans analizi yapabilmek için kampın en az 2 geçerli günü olmalıdır.")

# ── TAB 2: DAĞILIM (KUTU GRAFİĞİ) ─────────────────────────────────────────────
with tabs[1]:
    section_title("Kamp Zorluk ve Dağılım Analizi", "📊")
    info_box("Kutu grafiği (Box-plot), bir kamptaki değerlerin nasıl dağıldığını gösterir. Ortadaki çizgi medyanı, kutunun sınırları ise oyuncuların %50'sinin yığıldığı alanı temsil eder.")
    
    sel_dist_metric = st.selectbox("Dağılımı İncelenecek Metrik:", numeric_cols, format_func=lambda x: METRICS.get(x, {}).get('display', x).upper(), key="dist_metric")
    
    fig_box = px.box(
        df, 
        x='camp_name', 
        y=sel_dist_metric, 
        color='tip',
        color_discrete_map={'MATCH': '#0D0D0D', 'TRAINING': '#E30A17'},
        labels={'camp_name': 'Kamp Adı', sel_dist_metric: METRICS.get(sel_dist_metric, {}).get('display', sel_dist_metric).upper(), 'tip': 'Seans Tipi'},
        title=f"<b>{age_group} - Kamplara Göre {METRICS.get(sel_dist_metric, {}).get('display', sel_dist_metric).upper()} Dağılımı</b>"
    )
    fig_box.update_layout(template="plotly_white", xaxis={'categoryorder':'category ascending'}, title_font=dict(family='Bebas Neue', size=22))
    st.plotly_chart(fig_box, use_container_width=True)

# ── TAB 3: KORELASYON MATRİSİ ─────────────────────────────────────────────────
with tabs[2]:
    section_title("Metrikler Arası Korelasyon", "📉")
    info_box("Hangi metriklerin birbiriyle doğrudan ilişkili olduğunu gösterir. +1'e yaklaşan değerler doğru orantıyı (biri artarken diğeri artar), -1'e yaklaşan değerler ters orantıyı ifade eder.")
    
    corr_metrics = st.multiselect(
        "Korelasyona Dahil Edilecek Metrikler:", 
        numeric_cols, 
        default=[m for m in ['total_distance', 'metrage', 'smax_kmh', 'player_load', 'amp'] if m in numeric_cols],
        format_func=lambda x: METRICS.get(x, {}).get('display', x).upper()
    )
    
    if len(corr_metrics) > 1:
        corr_df = df[corr_metrics].corr().round(2)
        
        # Etiketleri anlaşılır isimlere çevir
        corr_df.columns = [METRICS.get(c, {}).get('display', c).upper() for c in corr_df.columns]
        corr_df.index = corr_df.columns
        
        fig_corr = px.imshow(
            corr_df, 
            text_auto=True, 
            aspect="auto",
            color_continuous_scale='RdBu_r', 
            zmin=-1, zmax=1,
            title="<b>KORELASYON ISI HARİTASI</b>"
        )
        fig_corr.update_layout(title_font=dict(family='Bebas Neue', size=22))
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.warning("Korelasyon oluşturmak için en az 2 metrik seçmelisiniz.")

# ── TAB 4: TREND (ZAMAN SERİSİ) ───────────────────────────────────────────────
with tabs[3]:
    section_title("Takım Ortalaması Trend Analizi", "📈")
    info_box("Zaman içinde takımın genel performans ortalamasının nasıl değiştiğini izleyin.")
    
    sel_trend_metric = st.selectbox("Trendi İzlenecek Metrik:", numeric_cols, format_func=lambda x: METRICS.get(x, {}).get('display', x).upper(), key="trend_metric")
    
    # Tarihe göre takım ortalamasını al
    trend_df = df.groupby(['tarih', 'tip'])[sel_trend_metric].mean().reset_index()
    trend_df = trend_df.sort_values('tarih')
    trend_df['tarih_str'] = trend_df['tarih'].dt.strftime('%d.%m.%Y')
    
    fig_trend = px.line(
        trend_df, 
        x='tarih_str', 
        y=sel_trend_metric, 
        markers=True,
        labels={'tarih_str': 'Tarih', sel_trend_metric: 'Takım Ortalaması'},
        title=f"<b>Günlük Takım Ortalaması - {METRICS.get(sel_trend_metric, {}).get('display', sel_trend_metric).upper()}</b>"
    )
    
    # Maç ve Antrenman noktalarını ayırmak için hover bilgisi ekle
    fig_trend.update_traces(
        line=dict(color='#E30A17', width=3), 
        marker=dict(size=8, color='#0D0D0D'),
        hovertemplate='<b>Tarih:</b> %{x}<br><b>Ortalama:</b> %{y:.1f}'
    )
    
    fig_trend.update_layout(template="plotly_white", xaxis_tickangle=-45, title_font=dict(family='Bebas Neue', size=22))
    st.plotly_chart(fig_trend, use_container_width=True)

st.markdown('<div class="tff-footer"><p>Rugby Performans Sistemi · İstatistik ve Raporlama Sistemi</p></div>', unsafe_allow_html=True)