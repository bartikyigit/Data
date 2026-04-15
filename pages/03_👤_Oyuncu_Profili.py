import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
from config import AGE_GROUPS, METRICS, PRIMARY_METRICS, DEFAULT_MINUTES
from database import db_manager
from styles import inject_styles, page_header, section_title, info_box, COLORS
from utils import (plot_player_performance_with_band, plot_player_radar,
                   calculate_player_stats, calculate_composite_score,
                   plot_percentile_gauge, build_stats_table,
                   generate_player_report_html, render_export_buttons, percentile_color)

# AÇIKLAMA: Oyuncu Profili Sayfa Yapılandırması
st.set_page_config(page_title="Oyuncu Profili | TFF", layout="wide")
inject_styles()

page_header("🏃", "OYUNCU PROFİLİ",
            "Bireysel performans · Takım İçi Sıralama · Atletik Performans Skorlaması · Rapor")

# ── Oyuncu ve Yaş Grubu Seçimi ───────────────────────────────────────────────
c1, c2 = st.columns([1, 2])
with c1:
    default_age = st.session_state.get('pp_age', AGE_GROUPS[0])
    age_index = AGE_GROUPS.index(default_age) if default_age in AGE_GROUPS else 0
    age_group = st.selectbox("YAŞ GRUBU", AGE_GROUPS, index=age_index, key="pp_age_sel")

with c2:
    players = db_manager.get_players(age_group)
    if not players:
        st.warning(f"{age_group} için oyuncu bulunamadı."); st.stop()
    default_player = st.session_state.get('pp_player', players[0])
    player_index = players.index(default_player) if default_player in players else 0
    selected_player = st.selectbox("OYUNCU SEÇİMİ", players, index=player_index, key="pp_player_sel")

# ── Dakika Filtreleri (Veri Kirliliğini Önler) ───────────────────────────────
with st.expander("⚙️ DAKİKA VE VERİ FİLTRELERİ", expanded=False):
    st.markdown("<div style='font-size:13px; color:#6B7280; margin-bottom:10px;'>Oyuncunun az süre aldığı seansların genel ortalamasını (Percentile) düşürmemesi için minimum dakika sınırlarını belirleyin.</div>", unsafe_allow_html=True)
    dk1, dk2 = st.columns(2)
    with dk1:
        min_train_dk = st.number_input("Minimum Antrenman Dakikası", value=DEFAULT_MINUTES['TRAINING'], step=5, key="pp_dk_tr")
    with dk2:
        min_match_dk = st.number_input("Minimum Maç Dakikası", value=DEFAULT_MINUTES['MATCH'], step=5, key="pp_dk_ma")

raw_age_data    = db_manager.get_data_by_age_group(age_group)
raw_player_data = db_manager.get_data_by_player(selected_player)

if raw_player_data.empty:
    st.warning("Oyuncuya ait veri bulunamadı."); st.stop()

# Filtreyi Uygula
def apply_minute_filter(df):
    if df.empty: return df
    is_tr = df['tip'].str.upper().str.contains('TRAINING')
    is_ma = df['tip'].str.upper().str.contains('MATCH')
    mask = (is_tr & (df['minutes'] >= min_train_dk)) | (is_ma & (df['minutes'] >= min_match_dk))
    return df[mask].copy()

age_data = apply_minute_filter(raw_age_data)
player_data = apply_minute_filter(raw_player_data)

if player_data.empty:
    st.warning("Belirlenen dakika filtrelerine uygun oyuncu verisi bulunamadı. Lütfen filtreyi düşürün.")
    st.stop()

stats = calculate_player_stats(player_data)

player_info = db_manager.get_player_info(selected_player)
photo_url = player_info.get('photo_url') if player_info.get('photo_url') else "https://cdn-icons-png.flaticon.com/512/847/847969.png"
club_logo_url = player_info.get('club_logo_url') if player_info.get('club_logo_url') else "https://upload.wikimedia.org/wikipedia/tr/b/b9/T%C3%BCrkiye_Futbol_Federasyonu_logo.png"

# ── Oyuncu Üst Kartı (Hero Section) ───────────────────────────────────────────
st.markdown(f"""
<div style="display: flex; align-items: center; background: #FFFFFF; border: 1px solid {COLORS['GRAY_200']}; border-radius: 16px; padding: 25px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.03);">
    <div style="position: relative; width: 140px; height: 140px; flex-shrink: 0;">
        <img src="{photo_url}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%; border: 4px solid #E30A17; background: #FAFAFA;">
        <div style="position: absolute; bottom: -5px; right: -5px; width: 48px; height: 48px; background: white; border-radius: 50%; padding: 5px; box-shadow: 0 3px 10px rgba(0,0,0,0.2); border: 1px solid #E5E7EB; display: flex; align-items: center; justify-content: center;">
            <img src="{club_logo_url}" style="width: 100%; height: 100%; object-fit: contain;">
        </div>
    </div>
    <div style="margin-left: 35px; flex-grow: 1;">
        <div style="font-family: 'Bebas Neue', sans-serif; font-size: 42px; color: {COLORS['GRAY_900']}; letter-spacing: 1.5px; line-height: 1.1;">
            {selected_player.upper()}
        </div>
        <div style="font-size: 15px; color: {COLORS['GRAY_500']}; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 5px;">
            🇹🇷 {age_group} MİLLİ TAKIMI
        </div>
        <div style="display: flex; gap: 15px; margin-top: 15px;">
            <div style="background: {COLORS['GRAY_50']}; border: 1px solid {COLORS['GRAY_200']}; border-radius: 10px; padding: 10px 20px;">
                <div style="font-size: 11px; color: {COLORS['GRAY_500']}; font-weight: 800; text-transform: uppercase;">Toplam Kamp</div>
                <div style="font-size: 22px; font-family:'Bebas Neue'; color: {COLORS['GRAY_800']}; letter-spacing: 1px;">{int(stats.get('camp_count', 0))}</div>
            </div>
            <div style="background: {COLORS['GRAY_50']}; border: 1px solid {COLORS['GRAY_200']}; border-radius: 10px; padding: 10px 20px;">
                <div style="font-size: 11px; color: {COLORS['GRAY_500']}; font-weight: 800; text-transform: uppercase;">Geçerli Gün</div>
                <div style="font-size: 22px; font-family:'Bebas Neue'; color: {COLORS['GRAY_800']}; letter-spacing: 1px;">{int(stats.get('session_count', 0))}</div>
            </div>
            <div style="background: {COLORS['GRAY_50']}; border: 1px solid {COLORS['GRAY_200']}; border-radius: 10px; padding: 10px 20px;">
                <div style="font-size: 11px; color: {COLORS['GRAY_500']}; font-weight: 800; text-transform: uppercase;">Max Hız (Genel)</div>
                <div style="font-size: 22px; font-family:'Bebas Neue'; color: #E30A17; letter-spacing: 1px;">{stats.get('max_speed', 0):.1f} <span style="font-size:12px; font-family:'DM Sans';">km/h</span></div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

camps_df  = db_manager.get_camps(age_group)
camp_dict = {}
for _, row in camps_df.iterrows():
    if row['camp_id'] in raw_player_data['camp_id'].values:
        label = row['camp_name']
        if pd.notna(row.get('start_date')):
            label += f"  ({str(row['start_date'])[:7]})"
        camp_dict[label] = row['camp_id']

cc1, cc2, cc3 = st.columns([2, 1, 1])
with cc1: sel_camp_label = st.selectbox("KAMP SEÇİMİ", list(camp_dict.keys()), key="pp_camp")
with cc2: ses = st.radio("SEANS TİPİ (GÖRÜNÜM İÇİN)", ["Tümü","TRAINING","MATCH"], horizontal=True, key="pp_ses")
with cc3: score_ses = st.radio("SKORLAMA BAZI (PERCENTILE)", ["Tümü","TRAINING","MATCH"], horizontal=True, key="pp_score_ses")

sel_camp_id      = camp_dict[sel_camp_label]
camp_player_data = player_data[player_data['camp_id'] == sel_camp_id].copy()
camp_team_data   = age_data[age_data['camp_id'] == sel_camp_id].copy()

if ses != "Tümü":
    camp_player_data = camp_player_data[camp_player_data['tip'].str.upper() == ses]
    camp_team_data   = camp_team_data[camp_team_data['tip'].str.upper() == ses]

score_dict = calculate_composite_score(camp_player_data, camp_team_data, session_filter=score_ses if score_ses != "Tümü" else "ALL")
composite  = score_dict.get('composite', 0)

safe_player_name = selected_player.replace(" ", "_")
safe_camp_name = sel_camp_label.split(" ")[0].replace(".", "_")

st.divider()

# ── Seçili Kamp Performansı ───────────────────────────────────────────────────
section_title("SEÇİLİ KAMP PERFORMANSI", "📊")
m1,m2,m3,m4,m5,m6,m7 = st.columns(7)
m_data = camp_player_data[camp_player_data['tip'].str.upper().str.contains('MATCH')]
t_data = camp_player_data[camp_player_data['tip'].str.upper().str.contains('TRAINING')]

with m1: st.markdown(f"<div class='metric-card' style='padding:12px;'><div class='sc-label'>GÜN</div><div class='sc-val' style='font-size:24px;'>{camp_player_data['tarih'].nunique()}</div></div>", unsafe_allow_html=True)
with m2: st.markdown(f"<div class='metric-card' style='padding:12px;'><div class='sc-label'>SEANS</div><div class='sc-val' style='font-size:24px;'>{len(camp_player_data)}</div></div>", unsafe_allow_html=True)
with m3: st.markdown(f"<div class='metric-card' style='padding:12px;'><div class='sc-label'>MAÇ GÜNÜ</div><div class='sc-val' style='font-size:24px;'>{m_data['tarih'].nunique() if not m_data.empty else 0}</div></div>", unsafe_allow_html=True)
with m4: st.markdown(f"<div class='metric-card' style='padding:12px;'><div class='sc-label'>ANTRENMAN</div><div class='sc-val' style='font-size:24px;'>{t_data['tarih'].nunique() if not t_data.empty else 0}</div></div>", unsafe_allow_html=True)
with m5: st.markdown(f"<div class='metric-card' style='padding:12px;'><div class='sc-label'>ORT. MESAFE</div><div class='sc-val' style='font-size:24px;'>{camp_player_data['total_distance'].mean():.0f} <span style='font-size:10px;color:#9CA3AF;'>m</span></div></div>", unsafe_allow_html=True)
with m6: st.markdown(f"<div class='metric-card' style='padding:12px;'><div class='sc-label'>MAX HIZ</div><div class='sc-val' style='font-size:24px;'>{camp_player_data['smax_kmh'].max():.1f} <span style='font-size:10px;color:#9CA3AF;'>km/h</span></div></div>", unsafe_allow_html=True)
with m7:
    c = percentile_color(composite)
    st.markdown(f"""
    <div style="background:white;border:1px solid {COLORS['GRAY_200']};border-radius:12px;
                padding:12px 10px;text-align:center;border-top:4px solid {c}; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
        <div style="font-size:10px;font-weight:800;text-transform:uppercase; color:{COLORS['GRAY_500']};">BİLEŞİK SKOR</div>
        <div style="font-family:'Bebas Neue',sans-serif;font-size:26px; color:{c}; margin-top:2px; letter-spacing: 1px;">{composite:.0f}%</div>
    </div>
    """, unsafe_allow_html=True)

avail_m = [m for m in PRIMARY_METRICS if m in camp_player_data.columns and camp_player_data[m].notna().any()]

# ── Yeni Tab Yapısı (6 Sekme) ────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈  PERFORMANS", 
    "🏆  TAKIM İÇİ SIRALAMA", 
    "📊  MİN/ORT/MAX", 
    "🎯  ATLETİK SKORLAMA", 
    "🔵  RADAR", 
    "📄  RAPOR KARTI"
])

# ── TAB 1: Performans Serisi ──────────────────────────────────────────────────
with tab1:
    for i in range(0, len(avail_m), 2):
        cols = st.columns(2)
        for j, metric in enumerate(avail_m[i:i+2]):
            with cols[j]:
                fig = plot_player_performance_with_band(camp_player_data, camp_team_data, metric)
                st.plotly_chart(fig, use_container_width=True)

# ── TAB 2: TAKIM İÇİ SIRALAMA (RENKLİ PANDAS STYLER) ──────────────────────────
with tab2:
    section_title("GÜNLÜK TAKIM İÇİ SIRALAMA VE DAĞILIM", "🏆", "Oyuncunun her seans için tüm takım içerisindeki konumunu (rank) gösterir.")
    
    if not avail_m:
        st.info("Bu kamp için yeterli metrik verisi bulunmuyor.")
    else:
        rank_metric = st.selectbox("İNCELENECEK METRİK", avail_m, format_func=lambda x: METRICS.get(x, {}).get('display', x).upper(), key="rank_metric")
        
        if rank_metric:
            valid_team_data = camp_team_data.dropna(subset=[rank_metric]).copy()
            dates = sorted(valid_team_data['tarih'].unique())
            rank_rows = []
            
            for dt in dates:
                d_df = valid_team_data[valid_team_data['tarih'] == dt].copy()
                if d_df.empty: continue
                
                d_df['_rank'] = d_df[rank_metric].rank(ascending=False, method='min').astype(int)
                
                p_row = d_df[d_df['player_name'] == selected_player]
                if not p_row.empty:
                    val = p_row[rank_metric].iloc[0]
                    rank = p_row['_rank'].iloc[0]
                    tip = p_row['tip'].iloc[0]
                    total_p = len(d_df)
                    team_avg = d_df[rank_metric].mean()
                    
                    rank_rows.append({
                        "TARİH": pd.Timestamp(dt).strftime('%d.%m.%Y'),
                        "TİP": "🔴 MAÇ" if 'MATCH' in str(tip).upper() else "⚫ ANTRENMAN",
                        "DEĞER": f"{val:.1f}",
                        "TAKIM İÇİ SIRA": f"#{rank} / {total_p}",
                        "TAKIM ORT.": f"{team_avg:.1f}",
                        "_raw_rank": rank,
                        "_raw_total": total_p
                    })
            
            fig_dist = go.Figure()
            
            other_players = valid_team_data[valid_team_data['player_name'] != selected_player]
            fig_dist.add_trace(go.Scatter(
                x=other_players['tarih'], 
                y=other_players[rank_metric],
                mode='markers',
                name='Diğer Oyuncular',
                marker=dict(color=COLORS['GRAY_300'], size=9, opacity=0.5, line=dict(width=1, color='white')),
                text=other_players['player_name'],
                hovertemplate="<b>%{text}</b><br>Tarih: %{x}<br>Değer: %{y}<extra></extra>"
            ))
            
            main_player = valid_team_data[valid_team_data['player_name'] == selected_player]
            fig_dist.add_trace(go.Scatter(
                x=main_player['tarih'], 
                y=main_player[rank_metric],
                mode='markers',
                name=selected_player.upper(),
                marker=dict(color=COLORS['GREEN'], size=18, symbol='star-diamond', line=dict(width=1.5, color='white')),
                hovertemplate=f"<b>{selected_player.upper()}</b><br>Tarih: %{{x}}<br>Değer: %{{y}}<extra></extra>"
            ))
            
            fig_dist.update_layout(
                title=dict(text=f"<b>{selected_player.upper()} - Takım İçi Konumu</b>", font=dict(family='Bebas Neue, sans-serif', size=22, color=COLORS['GRAY_800'])),
                xaxis=dict(title="", tickformat="%d.%m.%Y", gridcolor='#F3F4F6'),
                yaxis=dict(title=METRICS.get(rank_metric, {}).get('unit', ''), gridcolor='#F3F4F6'),
                plot_bgcolor='#FAFAFA', paper_bgcolor='white',
                legend=dict(orientation='h', yanchor='bottom', y=1.05, xanchor='right', x=1),
                margin=dict(t=70, b=40, l=40, r=40),
                height=450
            )
            
            st.plotly_chart(fig_dist, use_container_width=True)
            
            df_rank = pd.DataFrame(rank_rows)
            if not df_rank.empty:
                st.markdown("<div style='font-size:12px; color:#6B7280; margin-bottom:5px; font-weight:bold;'>SIRA RENK GÖSTERGESİ: &nbsp; 🟢 İlk %33 (Zirve) &nbsp;|&nbsp; 🟡 Orta %33 &nbsp;|&nbsp; 🔴 Son %33 (Gelişime Açık)</div>", unsafe_allow_html=True)

                def style_rank_col(row):
                    try:
                        pct = row['_raw_rank'] / row['_raw_total']
                        if pct <= 0.33:
                            color = 'background-color: rgba(34, 197, 94, 0.2); color: #166534; font-weight: bold;'
                        elif pct >= 0.67:
                            color = 'background-color: rgba(239, 68, 68, 0.2); color: #991b1b; font-weight: bold;'
                        else:
                            color = 'background-color: rgba(245, 158, 11, 0.2); color: #854d0e; font-weight: bold;'
                    except:
                        color = ''
                    return ['' if col != 'TAKIM İÇİ SIRA' else color for col in row.index]

                styled_df = df_rank.style.apply(style_rank_col, axis=1)
                
                st.dataframe(
                    styled_df, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "_raw_rank": None,
                        "_raw_total": None
                    }
                )
                
                clean_export_df = df_rank.drop(columns=['_raw_rank', '_raw_total'])
                render_export_buttons(df=clean_export_df, key_prefix="pp_rank", filename=f"{safe_player_name}_{safe_camp_name}_TakimIciSira")
            else:
                st.info("Bu metrik için geçerli bir sıralama verisi bulunmuyor.")

# ── TAB 3: Min / Ort / Max Tablosu & GÖRSEL KOMBİNASYONU ─────────────
with tab3:
    section_title("MİN / ORT / MAX PERFORMANS", "📊", tooltip="Oyuncunun kamp değerlerinin takım ile kıyaslanması.")
    
    mm_df = build_stats_table(camp_player_data, camp_team_data)
    
    # AÇIKLAMA: ZIRHLI SAYI AYIKLAMA (REGEX) FONKSİYONU
    def extract_num(val):
        if pd.isna(val): return None
        if isinstance(val, (int, float)): return float(val)
        s = str(val).replace(',', '.')
        matches = re.findall(r"[-+]?\d*\.\d+|\d+", s)
        return float(matches[0]) if matches else None

    # MİN/ORT/MAX GÖRSELLEŞTİRMESİ
    if not mm_df.empty:
        st.markdown("<h4 style='margin-top: 10px; color: #4B5563; font-family: DM Sans;'>Oyuncu Kapasitesi vs Takım Kapasitesi</h4>", unsafe_allow_html=True)
        
        # Sütun isimlerini dinamik tespit et
        col_metric = "METRİK" if "METRİK" in mm_df.columns else mm_df.columns[0]
        # utils tablosunda oyuncu verileri 2, 3 ve 4. sütunlardadır
        col_p_min = mm_df.columns[2]
        col_p_avg = mm_df.columns[3]
        col_p_max = mm_df.columns[4]
        
        chart_cols = st.columns(2)
        valid_charts_drawn = 0
        
        for i, row in mm_df.iterrows():
            m_name = row[col_metric]
            
            # Sayıya çevirmeye çalış
            p_min = extract_num(row[col_p_min])
            p_avg = extract_num(row[col_p_avg])
            p_max = extract_num(row[col_p_max])
            
            # Eğer NaN ise grafiği atla
            if p_min is None or p_max is None or p_avg is None: 
                continue
                
            fig = go.Figure()
            
            # Oyuncu Kapasite Çizgisi
            fig.add_trace(go.Scatter(
                x=[p_min, p_max],
                y=[m_name, m_name],
                mode='lines+markers',
                line=dict(color=COLORS['GRAY_300'], width=14),
                marker=dict(color=COLORS['GRAY_400'], size=14, symbol='line-ns'),
                hoverinfo='skip',
                showlegend=False
            ))
            
            # Oyuncu Ortalaması
            fig.add_trace(go.Scatter(
                x=[p_avg],
                y=[m_name],
                mode='markers',
                marker=dict(color=COLORS['GREEN'], size=20, symbol='circle', line=dict(color='white', width=2)),
                name='Ortalama',
                hovertemplate=f"<b>{m_name}</b><br>Min: {p_min:.1f}<br>Ort: {p_avg:.1f}<br>Max: {p_max:.1f}<extra></extra>",
                showlegend=False
            ))
            
            diff = p_max - p_min
            padding = diff * 0.15 if diff > 0 else (p_min * 0.1 if p_min > 0 else 1)
            
            fig.update_layout(
                title=dict(text=f"<b>{m_name}</b>", font=dict(family='DM Sans', size=14, color=COLORS['GRAY_800'])),
                xaxis=dict(range=[p_min - padding, p_max + padding], showgrid=True, gridcolor='#F3F4F6'),
                yaxis=dict(showticklabels=False, showgrid=False),
                plot_bgcolor='white', paper_bgcolor='white',
                height=130,
                margin=dict(l=10, r=20, t=35, b=15)
            )
            
            with chart_cols[valid_charts_drawn % 2]:
                st.plotly_chart(fig, use_container_width=True)
            
            valid_charts_drawn += 1
            
    st.divider()
    st.dataframe(mm_df, use_container_width=True, hide_index=True)
    # HATA BURADA ÇÖZÜLDÜ: safe_player_name doğru şekilde çağırıldı
    render_export_buttons(df=mm_df, key_prefix="pp_mm", filename=f"{safe_player_name}_{safe_camp_name}_MinOrtMax")

# ── TAB 4: Percentile & Yapay Zeka Yorumu ────────────────────────────────────
with tab4:
    section_title("ATLETİK PERFORMANS SKORLAMASI (PERCENTILE)", "🎯", 
                  tooltip="Oyuncunun her bir metrikteki performansı...")

    pct_metrics = [m for m in PRIMARY_METRICS if m in camp_player_data.columns and camp_player_data[m].dropna().any()]
    
    if not pct_metrics:
        st.warning("Bu oyuncu için skorlanabilecek metrik verisi bulunamadı.")
    else:
        st.divider()
        cols_count = min(len(pct_metrics), 4)
        gauge_cols = st.columns(cols_count)
        
        for i, m in enumerate(pct_metrics):
            with gauge_cols[i % 4]:
                pct = score_dict.get(m, 50)
                label = METRICS.get(m, {}).get('display', m)
                fig = plot_percentile_gauge(pct, label)
                st.plotly_chart(fig, use_container_width=True)

# ── TAB 5: Radar Grafiği ─────────────────────────────────────────────────────
with tab5:
    if not camp_team_data.empty:
        fig_r = plot_player_radar(camp_player_data, camp_team_data)
        st.plotly_chart(fig_r, use_container_width=True)
        render_export_buttons(fig=fig_r, key_prefix="pp_radar", filename=f"{safe_player_name}_{safe_camp_name}_Radar")

# # ── TAB 6: Çoklu Kamp Rapor Kartı (GELİŞTİRİLDİ VE HATASI ÇÖZÜLDÜ) ────────────
with tab6:
    report_camps = st.multiselect("RAPORA DAHİL EDİLECEK KAMPLAR", options=list(camp_dict.keys()), default=[sel_camp_label], key="report_camps")
    if report_camps:
        report_camp_ids = [camp_dict[c] for c in report_camps]
        report_p_data = player_data[player_data['camp_id'].isin(report_camp_ids)].copy()
        report_t_data = age_data[age_data['camp_id'].isin(report_camp_ids)].copy()
        rep_stats = calculate_player_stats(report_p_data)
        rep_score_dict = calculate_composite_score(report_p_data, report_t_data, session_filter=score_ses if score_ses != "Tümü" else "ALL")

        # --- YENİ EKLENTİ: RAPOR ÖNCESİ HIZLI SKOR GÖRSELLEŞTİRMESİ ---
        st.markdown("<h4 style='color: #1F2937; margin-bottom: 15px;'>Seçili Kamplara Göre Skor Özeti</h4>", unsafe_allow_html=True)
        
        comp_val = rep_score_dict.get('composite', 0)
        c_color = percentile_color(comp_val)
        
        sc_col1, sc_col2 = st.columns([1, 3])
        with sc_col1:
            st.markdown(f"<div style='background:white;border:2px solid {COLORS['GRAY_200']};border-radius:12px;padding:20px;text-align:center;box-shadow: 0 4px 6px rgba(0,0,0,0.05);'><div style='font-size:12px;font-weight:800;color:{COLORS['GRAY_500']};'>BİLEŞİK SKOR</div><div style='font-family:\"Bebas Neue\",sans-serif;font-size:48px; color:{c_color}; margin-top:5px;'>{comp_val:.0f}%</div><div style='font-size:10px;color:{COLORS['GRAY_400']};margin-top:5px;'>Takımın %{comp_val:.0f}'sinden daha iyi</div></div>", unsafe_allow_html=True)
            
        with sc_col2:
            bars_html = "<div style='display:flex; flex-direction:column; gap:10px;'>"
            for m in PRIMARY_METRICS:
                if m in rep_score_dict and m != 'composite':
                    val = rep_score_dict[m]
                    m_label = METRICS.get(m, {}).get('display', m).upper()
                    bar_color = percentile_color(val)
                    
                    # HATA ÇÖZÜMÜ: HTML kodları başlarında boşluk kalmaması için tek tek eklendi
                    bars_html += f"<div style='display:flex; align-items:center; font-family:\"DM Sans\",sans-serif;'>"
                    bars_html += f"<div style='width:150px; font-size:11px; font-weight:bold; color:{COLORS['GRAY_700']};'>{m_label}</div>"
                    bars_html += f"<div style='flex-grow:1; background:{COLORS['GRAY_200']}; height:10px; border-radius:5px; margin:0 15px; overflow:hidden;'>"
                    bars_html += f"<div style='width:{val}%; background:{bar_color}; height:100%; border-radius:5px;'></div>"
                    bars_html += f"</div>"
                    bars_html += f"<div style='width:40px; font-size:12px; font-weight:bold; color:{bar_color}; text-align:right;'>{val:.0f}%</div>"
                    bars_html += f"</div>"
                    
            bars_html += "</div>"
            st.markdown(bars_html, unsafe_allow_html=True)
            
        st.divider()

        html_report = generate_player_report_html(
            player_name=selected_player, age_group=age_group, stats=rep_stats, score_dict=rep_score_dict,
            player_data=report_p_data, team_data=report_t_data,
            camp_name=" + ".join([c.split(" ")[0] for c in report_camps]),
            photo_url=photo_url, club_logo_url=club_logo_url
        )
        render_export_buttons(html_report=html_report, key_prefix="pp_report", filename=f"{age_group}_{safe_player_name}_Rapor")
        
        with st.expander("📄 RAPOR ÖNİZLEMESİ", expanded=True):
            st.components.v1.html(html_report, height=700, scrolling=True)

st.markdown('<div class="tff-footer"><p>Rugby Performans Sistemi · Oyuncu Profili Analizi</p></div>', unsafe_allow_html=True)