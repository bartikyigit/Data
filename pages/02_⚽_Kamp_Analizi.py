import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
from config import AGE_GROUPS, METRICS, PRIMARY_METRICS, DEFAULT_MINUTES
from database import db_manager
from styles import inject_styles, page_header, section_title, info_box, COLORS
from utils import render_export_buttons, plot_day_comparison, build_stats_table

# AÇIKLAMA: Kamp analiz sayfasının temel yapılandırması
st.set_page_config(page_title="Kamp Analizi | Bursaspor", layout="wide")
inject_styles()
page_header("⚽", "KAMP ANALİZİ",
            "Günlük & kamp bazlı sıralamalar · Min / Ort / Max · Gün karşılaştırma")

# AÇIKLAMA: En üstte kullanıcıyı yönlendiren genel bir bilgi mesajı
info_box("Bu sayfada seçtiğiniz yaş grubu ve kampa ait tüm verileri takım bazında analiz edebilirsiniz. Lütfen verilerin doğruluğu için aşağıdaki 'Dakika ve Veri Filtreleri' menüsünden antrenman ve maç sürelerini ayarlamayı unutmayın.")

# ── Filtreler ─────────────────────────────────────────────────────────────────
# AÇIKLAMA: Yaş grubu, Kamp ve Seans tipini (Maç/Antrenman) filtrelemek için arayüz
with st.container():
    f1, f2, f3 = st.columns([1, 2, 1])
    with f1:
        age_group = st.selectbox("YAŞ GRUBU", AGE_GROUPS, key="ca_age")
    try:
        camps_df = db_manager.get_camps(age_group)
        if camps_df.empty:
            st.warning("Bu yaş grubu için kamp bulunamadı.")
            st.stop()
        camp_options = {row['camp_name']: row['camp_id'] for _, row in camps_df.iterrows()}
    except Exception as e:
        st.error(str(e)); st.stop()

    with f2:
        selected_camp_name = st.selectbox("KAMP SEÇİMİ", list(camp_options.keys()), key="ca_camp")
    with f3:
        session_types = st.multiselect("SEANS TİPİ", ['TRAINING','MATCH'],
                                       default=['TRAINING','MATCH'], key="ca_ses")

# Dakika Filtreleri (Veri Kirliliğini Önler)
with st.expander("⚙️ DAKİKA VE VERİ FİLTRELERİ (Gelişmiş)", expanded=False):
    st.markdown("<div style='font-size:13px; color:#6B7280; margin-bottom:10px;'>Ortalamaları ve minimum değerleri çarpıtmaması için, belirli bir dakikanın altında oynayan oyuncuları analizden çıkarabilirsiniz. <strong>Sistemin sağlıklı çalışması için bu filtreleri kamp dinamiklerinize göre ayarlamayı unutmayın.</strong></div>", unsafe_allow_html=True)
    dk1, dk2 = st.columns(2)
    with dk1:
        min_train_dk = st.number_input("Minimum Antrenman Dakikası", value=DEFAULT_MINUTES['TRAINING'], step=5)
    with dk2:
        min_match_dk = st.number_input("Minimum Maç Dakikası", value=DEFAULT_MINUTES['MATCH'], step=5)

camp_id   = camp_options[selected_camp_name]
camp_data = db_manager.get_data_by_camp(camp_id)

filtered_by_session = camp_data[camp_data['tip'].isin(session_types)] if session_types else camp_data

is_training = filtered_by_session['tip'].str.upper().str.contains('TRAINING')
is_match = filtered_by_session['tip'].str.upper().str.contains('MATCH')

valid_mask = (is_training & (filtered_by_session['minutes'] >= min_train_dk)) | \
             (is_match & (filtered_by_session['minutes'] >= min_match_dk))

filtered = filtered_by_session[valid_mask].copy()

if filtered.empty:
    st.warning("Seçilen filtrelere (Dakika / Seans) uygun veri bulunamadı. Lütfen filtreleri esnetin.")
    st.stop()

avail_dates = sorted(filtered['tarih'].dropna().unique())
avail_m = [m for m in PRIMARY_METRICS if m in filtered.columns]

safe_camp_name = selected_camp_name.replace(" ", "_").replace(".", "")

st.divider()

# ── KAMP ÖZETİ (PROFESYONEL HTML KARTLAR) ────────────────────────────────────
section_title("KAMP ÖZETİ", "📊")

match_days = filtered[filtered['tip'].str.upper().str.contains('MATCH')]['tarih'].nunique()
train_days = filtered[filtered['tip'].str.upper().str.contains('TRAINING')]['tarih'].nunique()
unique_players = filtered['player_name'].nunique()
total_days = filtered['tarih'].nunique()
avg_dist = filtered['total_distance'].mean() if 'total_distance' in filtered else 0
max_spd = filtered['smax_kmh'].max() if 'smax_kmh' in filtered else 0

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

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1: st.markdown(render_kpi_card("Oyuncu", unique_players), unsafe_allow_html=True)
with c2: st.markdown(render_kpi_card("Toplam Gün", total_days), unsafe_allow_html=True)
with c3: st.markdown(render_kpi_card("Maç Günü", match_days), unsafe_allow_html=True)
with c4: st.markdown(render_kpi_card("Antrenman", train_days), unsafe_allow_html=True)
with c5: st.markdown(render_kpi_card("Ort. Mesafe", f"{avg_dist:.0f}", "m"), unsafe_allow_html=True)
with c6: st.markdown(render_kpi_card("Max Hız", f"{max_spd:.1f}", "km/h"), unsafe_allow_html=True)

st.divider()

# ── GÖRSEL KAMP TAKVİMİ ──────────────────────────────────────────────────────
section_title("KAMP PROGRAMI (TAKVİM)", "📅")

if len(avail_dates) > 0:
    timeline_html = "<div style='display:flex; overflow-x:auto; gap:12px; padding:10px 5px; margin-bottom:15px; white-space:nowrap;'>"
    for dt in avail_dates:
        d_df = filtered[filtered['tarih'] == dt]
        if d_df.empty: continue
        
        tip = str(d_df['tip'].iloc[0]).upper()
        is_match = 'MATCH' in tip
        
        color = COLORS['GREEN'] if is_match else COLORS['BLACK']
        bg_color = 'rgba(0,122,51,0.06)' if is_match else 'rgba(13,13,13,0.04)'
        label = '🔴 MAÇ GÜNÜ' if is_match else '⚫ ANTRENMAN'
        
        ts = pd.Timestamp(dt)
        date_str = ts.strftime('%d.%m.%Y')
        
        timeline_html += f"<div style='display:inline-block; min-width:130px; border:1px solid {color}; border-top:5px solid {color}; border-radius:10px; text-align:center; padding:12px 8px; background:{bg_color}; box-shadow: 0 4px 6px rgba(0,0,0,0.03); transition: transform 0.2s;' onmouseover=\"this.style.transform='translateY(-2px)'\" onmouseout=\"this.style.transform='translateY(0)'\"><div style='font-size:13px; color:{COLORS['GRAY_800']}; font-weight:800;'>{date_str}</div><div style='font-size:16px; font-family:\"Bebas Neue\", sans-serif; color:{color}; letter-spacing:1px; margin-top:6px;'>{label}</div></div>"
        
    timeline_html += "</div>"
    st.markdown(timeline_html, unsafe_allow_html=True)
    st.caption("☝️ *Takvim şeridinden programı inceleyip, analizi detaylandırmak için aşağıdaki sekmeleri kullanabilirsiniz.*")

st.divider()

# ── Tab Yapısı ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📅  GÜNLÜK SIRALAMA",
    "🔁  GÜN KARŞILAŞTIRMA",
    "📋  KAMP GENEL SIRALAMA",
    "📊  MİN / ORT / MAX TABLOSU",
])

# ── TAB 1: Günlük Sıralama ────────────────────────────────────────────────────
with tab1:
    section_title("GÜNLÜK SIRALAMA VE ANALİZ", "📉")
    d1, d2, d3 = st.columns([2, 2, 1])
    with d1:
        if not avail_dates:
            st.stop()
        selected_date = st.selectbox("İNCELENECEK TARİHİ SEÇİN", avail_dates, format_func=lambda x: pd.Timestamp(x).strftime('%d.%m.%Y') if x else "—", key="ca_date")
    with d2:
        selected_metric = st.selectbox("METRİK SEÇİMİ", avail_m, format_func=lambda x: METRICS.get(x,{}).get('display', x).upper(), key="ca_metric")
    with d3:
        ascending = st.radio("SIRALAMA YÖNÜ", ["↓ AZALAN (Büyükten Küçüğe)","↑ ARTAN (Küçükten Büyüğe)"], horizontal=False, key="ca_asc")

    if selected_date is None:
        st.info("Lütfen bir tarih seçin.")
        st.stop()

    sel_ts   = pd.Timestamp(selected_date)
    date_str = sel_ts.strftime('%d_%m_%Y')
    disp_date_str = sel_ts.strftime('%d.%m.%Y')
    
    day_data = filtered[filtered['tarih'].dt.normalize() == sel_ts.normalize()].copy()

    if day_data.empty:
        st.warning(f"{disp_date_str} tarihi için genel seans verisi bulunamadı.")
    else:
        valid_day_data = day_data.dropna(subset=[selected_metric]).copy()

        if valid_day_data.empty:
            metric_name = METRICS.get(selected_metric, {}).get('display', selected_metric).upper()
            st.info(f"💡 **{disp_date_str}** tarihinde **{metric_name}** metriği için sisteme henüz geçerli veri girilmemiş.")
        else:
            valid_day_data['_rank'] = valid_day_data[selected_metric].rank(ascending=False, method='min').astype(int)
            asc_bool = (ascending == "↑ ARTAN (Küçükten Büyüğe)")
            valid_day_data = valid_day_data.sort_values(selected_metric, ascending=asc_bool).reset_index(drop=True)
            
            m_info       = METRICS.get(selected_metric, {})
            metric_label = m_info.get('display', selected_metric).upper()
            metric_unit  = m_info.get('unit', '')
            n            = len(valid_day_data)
            
            valid_for_min = valid_day_data[selected_metric].replace(0, pd.NA).dropna()
            min_val      = valid_for_min.min() if not valid_for_min.empty else 0.0
            avg_val      = valid_day_data[selected_metric].mean()
            max_val      = valid_day_data[selected_metric].max()

            mm1, mm2, mm3 = st.columns(3)
            with mm1: st.markdown(render_kpi_card("Min Değer", f"{min_val:.1f}", metric_unit), unsafe_allow_html=True)
            with mm2: st.markdown(render_kpi_card("Ortalama", f"{avg_val:.1f}", metric_unit), unsafe_allow_html=True)
            with mm3: st.markdown(render_kpi_card("Max Değer", f"{max_val:.1f}", metric_unit), unsafe_allow_html=True)

            bar_colors = []
            for i, tip in enumerate(valid_day_data['tip']):
                fade = max(0.4, 1.0 - (i / max(n-1, 1)) * 0.55)
                if 'MATCH' in str(tip).upper():
                    bar_colors.append(f"rgba(13,13,13,{fade})") # Siyah (Bursaspor)
                else:
                    bar_colors.append(f"rgba(0,122,51,{fade})") # Yeşil (Bursaspor)

            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=valid_day_data['player_name'].str.upper(), x=valid_day_data[selected_metric], orientation='h',
                marker=dict(color=bar_colors, line=dict(color='rgba(0,0,0,0.06)', width=1)),
                text=[f"  #{r}   {v:.1f} {metric_unit}" for r, v in zip(valid_day_data['_rank'], valid_day_data[selected_metric])],
                textposition='inside', insidetextanchor='start',
                textfont=dict(color='white', size=12, family='DM Sans, sans-serif', weight='bold'),
                hovertemplate='<b>%{y}</b><br><b>%{x:.2f}</b> ' + metric_unit + '<extra></extra>',
            ))
            
            fig.add_vline(x=avg_val, line_dash="dash", line_color=COLORS['GRAY_500'], line_width=2,
                          annotation_text=f"ORT: {avg_val:.1f}", annotation_position="top right", annotation_font=dict(size=11, color=COLORS['GRAY_700'], weight='bold'))

            fig.update_layout(
                title=dict(text=f"<b>{disp_date_str} · {metric_label}</b>", font=dict(family='Bebas Neue, sans-serif', size=24, color=COLORS['GRAY_900'])),
                xaxis=dict(title=metric_unit, gridcolor='#F3F4F6', tickfont=dict(family='DM Sans', size=11, weight='bold')),
                yaxis=dict(title='', autorange="reversed", tickfont=dict(family='DM Sans', size=12, color=COLORS['GRAY_800'], weight='bold')),
                template='plotly_white', height=max(450, n * 35), showlegend=False, plot_bgcolor='#FAFAFA', paper_bgcolor=COLORS['WHITE'], margin=dict(l=20, r=60, t=60, b=40),
            )
            st.plotly_chart(fig, use_container_width=True)

            disp = valid_day_data[['_rank','player_name','tip','minutes',selected_metric]].copy()
            disp.columns = ['SIRA','OYUNCU','TİP','DAKİKA', metric_label]
            export_filename = f"{age_group}_{safe_camp_name}_{date_str}_{metric_label.replace(' ', '_')}"
            render_export_buttons(fig=fig, df=disp, key_prefix="ca_day", filename=export_filename)

# ── TAB 2: Gün Karşılaştırma ─────────────────────────────────────────────────
with tab2:
    section_title("GÜN KARŞILAŞTIRMA", "🔁")
    info_box("Aynı kamp içinden iki farklı günü seçerek oyuncu performanslarını karşılaştırın.")
    g1, g2, g3 = st.columns(3)
    with g1: day1 = st.selectbox("1. GÜN", avail_dates, format_func=lambda x: pd.Timestamp(x).strftime('%d.%m.%Y') if x else "—", key="dc_d1")
    with g2: day2 = st.selectbox("2. GÜN", avail_dates, index=min(1, len(avail_dates)-1), format_func=lambda x: pd.Timestamp(x).strftime('%d.%m.%Y') if x else "—", key="dc_d2")
    with g3: dc_metric = st.selectbox("METRİK SEÇİMİ", avail_m, format_func=lambda x: METRICS.get(x,{}).get('display', x).upper(), key="dc_metric")

    if day1 and day2 and day1 != day2:
        fig_dc = plot_day_comparison(filtered, day1, day2, dc_metric)
        st.plotly_chart(fig_dc, use_container_width=True)

# ── TAB 3: Kamp Genel Sıralama ───────────────────────────────────────────────
with tab3:
    section_title("KAMP GENEL SIRALAMASI (ORTALAMA DEĞERLER)", "📋")
    info_box("Bu sekme, kamp boyunca her oyuncunun katıldığı tüm geçerli seansların (maç+antrenman) aritmetik ortalamasını alarak Kamp Sonu Liderlik tablosunu oluşturur.")
    
    sum_m = [m for m in PRIMARY_METRICS if m in filtered.columns]
    
    summary = filtered.groupby('player_name')[sum_m].mean().round(1).fillna(0)
    
    sort_metric = 'total_distance' if 'total_distance' in summary.columns else sum_m[0]
    summary = summary.sort_values(sort_metric, ascending=False).reset_index()
    
    summary['SIRA'] = summary.index + 1
    summary['SIRA'] = summary['SIRA'].apply(lambda x: "🥇 1." if x==1 else ("🥈 2." if x==2 else ("🥉 3." if x==3 else f"{x}.")))
    
    rename = {m: METRICS.get(m, {}).get('display', m).upper() for m in sum_m}
    summary = summary.rename(columns=rename)
    
    col_config = {
        "SIRA": st.column_config.TextColumn("SIRA", width="small"),
        "player_name": st.column_config.TextColumn("OYUNCU ADI", width="medium")
    }
    
    for m in sum_m:
        display_name = METRICS.get(m, {}).get('display', m).upper()
        raw_max = summary[display_name].max()
        max_val = float(raw_max) if pd.notnull(raw_max) and raw_max > 0 else 100.0
        
        col_config[display_name] = st.column_config.ProgressColumn(
            display_name,
            help=f"Kamp Ortalama {display_name}",
            format="%.1f",
            min_value=0,
            max_value=max_val,
        )
        
    disp_cols = ['SIRA', 'player_name'] + list(rename.values())
    final_df = summary[disp_cols].replace([float('inf'), float('-inf')], 0).fillna(0)
    
    st.dataframe(final_df, use_container_width=True, hide_index=True, column_config=col_config)
    render_export_buttons(df=summary, key_prefix="ca_sum", filename=f"{age_group}_{safe_camp_name}_Genel_Siralama")
    
# ── TAB 4: Min / Ort / Max Tablosu & GÖRSEL (TAMAMEN ZIRHLI) ──────────────────
with tab4:
    section_title("KAMP MİN / ORT / MAX — OYUNCU BAZLI", "📊", 
                  tooltip="Oyuncunun o kamp boyunca ulaştığı en düşük, ortalama ve en yüksek değerleri gösterir.")
    info_box("Aşağıdaki grafikler ve tablo, seçilen oyuncunun ilgili kamptaki performans aralığını gösterir. Kalın gri çizgi oyuncunun ulaştığı Min-Max kapasitesini, yeşil nokta ise Ortalamasını temsil eder.")
    
    sel_player_mm = st.selectbox("OYUNCU SEÇ", sorted(filtered['player_name'].unique()), key="ca_mm_player")
    p_data   = filtered[filtered['player_name'] == sel_player_mm]
    
    mm_df = build_stats_table(p_data, filtered)
    
    # AÇIKLAMA: ZIRHLI SAYI AYIKLAMA (REGEX) FONKSİYONU
    # Tablodaki "24.5 km/h" veya "10,2" gibi birimli/karmaşık verilerin içinden sadece sayıyı çeker.
    def extract_num(val):
        if pd.isna(val): return None
        if isinstance(val, (int, float)): return float(val)
        s = str(val).replace(',', '.')
        matches = re.findall(r"[-+]?\d*\.\d+|\d+", s)
        return float(matches[0]) if matches else None

    if not mm_df.empty:
        st.markdown("<h4 style='margin-top: 10px; color: #4B5563; font-family: DM Sans;'>Performans Kapasite Aralıkları</h4>", unsafe_allow_html=True)
        
        col_metric = "METRİK" if "METRİK" in mm_df.columns else mm_df.columns[0]
        col_min = "OYUNCU MİN" if "OYUNCU MİN" in mm_df.columns else mm_df.columns[2]
        col_avg = "OYUNCU ORT." if "OYUNCU ORT." in mm_df.columns else mm_df.columns[3]
        col_max = "OYUNCU MAX" if "OYUNCU MAX" in mm_df.columns else mm_df.columns[4]
        
        chart_cols = st.columns(2)
        valid_charts_drawn = 0
        
        for i, row in mm_df.iterrows():
            m_name = row[col_metric]
            min_v = extract_num(row.get(col_min))
            avg_v = extract_num(row.get(col_avg))
            max_v = extract_num(row.get(col_max))
            
            if min_v is None or max_v is None or avg_v is None: 
                continue
                
            fig = go.Figure()
            
            # Kapasite Aralığı (Kalın Gri Çizgi)
            fig.add_trace(go.Scatter(
                x=[min_v, max_v],
                y=[m_name, m_name],
                mode='lines+markers',
                line=dict(color=COLORS['GRAY_200'], width=16),
                marker=dict(color=COLORS['GRAY_300'], size=16, symbol='line-ns'),
                hoverinfo='skip',
                showlegend=False
            ))
            
            # Ortalama (Yeşil Büyük Nokta - Bursaspor)
            fig.add_trace(go.Scatter(
                x=[avg_v],
                y=[m_name],
                mode='markers',
                marker=dict(color=COLORS['GREEN'], size=22, symbol='circle', line=dict(color='white', width=3)),
                name='Ortalama',
                hovertemplate=f"<b>{m_name}</b><br>Min: {min_v:.1f}<br>Ort: {avg_v:.1f}<br>Max: {max_v:.1f}<extra></extra>",
                showlegend=False
            ))
            
            diff = max_v - min_v
            padding = diff * 0.15 if diff > 0 else (min_v * 0.1 if min_v > 0 else 1)
            
            fig.update_layout(
                title=dict(text=f"<b>{m_name}</b>", font=dict(family='DM Sans', size=14, color=COLORS['GRAY_800'])),
                xaxis=dict(range=[min_v - padding, max_v + padding], showgrid=True, gridcolor='#F3F4F6'),
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
    render_export_buttons(df=mm_df, key_prefix="ca_mm", filename=f"{sel_player_mm}_{safe_camp_name}_MinOrtMax")

st.markdown('<div class="tff-footer"><p>Bursaspor Veri Merkezi · Kamp Analizi</p></div>', unsafe_allow_html=True)