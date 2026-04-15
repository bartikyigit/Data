import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from config import AGE_GROUPS, METRICS, RADAR_METRICS, PRIMARY_METRICS, DEFAULT_MINUTES
from database import db_manager
from styles import inject_styles, page_header, section_title, info_box, COLORS
from utils import (render_export_buttons, plot_player_comparison,
                   plot_radar_comparison_multiple, plot_camp_comparison,
                   calculate_percentile_rank, calculate_composite_score,
                   percentile_color, PLAYER_PALETTE)

# AÇIKLAMA: Karşılaştırma modülünün sayfa yapılandırması
st.set_page_config(page_title="Karşılaştırma | TFF", layout="wide")
inject_styles()
page_header("⚔️", "KARŞILAŞTIRMA VE FARK ANALİZİ",
            "H2H (Kafa Kafaya) · Çapraz Yaş Grubu · Kamp Karşılaştırma · Çoklu Radar")

# AÇIKLAMA: Analitik kullanım rehberi
info_box("Bu modül, oyuncuları birbirleriyle (H2H), farklı kampların performanslarını kendi aralarında ve oyuncuların çoklu radar profillerini kıyaslamak için kullanılır. 'Çapraz Yaş Grubu' özelliğiyle farklı kategorilerdeki (Örn: 71U vs 91U) oyuncuları çarpıştırabilir, aralarındaki fark yüzdelerini görebilirsiniz.")

# ── Ana Kontrol Paneli (Dakika Filtreleri) ───────────────────────────────────
with st.expander("⚙️ DAKİKA VE VERİ FİLTRELERİ (Gelişmiş)", expanded=False):
    st.markdown("<div style='font-size:13px; color:#6B7280; margin-bottom:10px;'>Karşılaştırma adaletsizliğini önlemek için az süre alınan seansları filtreleyebilirsiniz.</div>", unsafe_allow_html=True)
    dk1, dk2 = st.columns(2)
    with dk1: min_train_dk = st.number_input("Minimum Antrenman Dakikası", value=DEFAULT_MINUTES['TRAINING'], step=5, key="cmp_dk_tr")
    with dk2: min_match_dk = st.number_input("Minimum Maç Dakikası", value=DEFAULT_MINUTES['MATCH'], step=5, key="cmp_dk_ma")

def apply_minute_filter(df):
    if df.empty: return df
    is_tr = df['tip'].str.upper().str.contains('TRAINING')
    is_ma = df['tip'].str.upper().str.contains('MATCH')
    mask = (is_tr & (df['minutes'] >= min_train_dk)) | (is_ma & (df['minutes'] >= min_match_dk))
    return df[mask].copy()

# AÇIKLAMA: Ana navigasyon ve Modül Seçimi
cmp_type = st.radio(
    "KARŞILAŞTIRMA TİPİ",
    ["👥 İKİ OYUNCU H2H (Çapraz Yaş)", "🔁 KAMP KARŞILAŞTIRMA", "⚔️ ÇOKLU RADAR"],
    horizontal=True, key="cmp_type"
)
st.divider()

try:
    # ════════════════════════════════════════════════════════════════════════
    # MODÜL 1: H2H (KAFA KAFAYA KARŞILAŞTIRMA - ÇAPRAZ YAŞ DESTEKLİ)
    # ════════════════════════════════════════════════════════════════════════
    if cmp_type == "👥 İKİ OYUNCU H2H (Çapraz Yaş)":
        section_title("İKİ OYUNCU H2H KARŞILAŞTIRMASI", "👥", tooltip="Seçilen iki oyuncunun aynı şartlar altındaki performanslarını kafa kafaya kıyaslar. Farklı yaş grupları seçilebilir.")
        
        # AÇIKLAMA: Çapraz yaş grubu (Cross-Age) kıyaslama arayüzü
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<div style='color:#E30A17; font-weight:bold; margin-bottom:5px;'>🔴 1. OYUNCU SEÇİMİ</div>", unsafe_allow_html=True)
            age1 = st.selectbox("1. Oyuncu Yaş Grubu", AGE_GROUPS, key="cmp_age1")
            players1 = db_manager.get_players(age1)
            p1 = st.selectbox("1. Oyuncuyu Seçin", players1 if players1 else ["Veri Yok"], key="cmp_p1")
            
        with c2:
            st.markdown("<div style='color:#111827; font-weight:bold; margin-bottom:5px;'>⚫ 2. OYUNCU SEÇİMİ</div>", unsafe_allow_html=True)
            age2 = st.selectbox("2. Oyuncu Yaş Grubu", AGE_GROUPS, key="cmp_age2")
            players2 = db_manager.get_players(age2)
            p2 = st.selectbox("2. Oyuncuyu Seçin", players2 if players2 else ["Veri Yok"], index=min(1, len(players2)-1) if players2 else 0, key="cmp_p2")

        if not players1 or not players2 or p1 == "Veri Yok" or p2 == "Veri Yok":
            st.warning("Seçilen yaş gruplarında yeterli oyuncu verisi bulunamadı."); st.stop()
        if p1 == p2 and age1 == age2:
            st.warning("Lütfen farklı iki oyuncu seçin."); st.stop()

        f1, f2, f3 = st.columns(3)
        with f1: camp_filter = st.checkbox("Aynı/Belirli bir kampa sınırla", key="cmp_cf")
        with f2: ses = st.radio("Seans Tipi", ["Tümü","TRAINING","MATCH"], horizontal=True, key="cmp_ses")
        with f3: show_team = st.checkbox("Takım ortalamasını grafikte göster", value=True, key="cmp_team")

        # Verileri veritabanından çek ve dakikaya göre temizle
        p1_raw = db_manager.get_data_by_player(p1)
        p2_raw = db_manager.get_data_by_player(p2)
        p1d = apply_minute_filter(p1_raw)
        p2d = apply_minute_filter(p2_raw)
        
        # Takım verileri (Kıyaslama için)
        t1d = apply_minute_filter(db_manager.get_data_by_age_group(age1))
        t2d = apply_minute_filter(db_manager.get_data_by_age_group(age2))

        # Kamp filtrelemesi
        if camp_filter:
            common_camps = list(set(p1d['camp_id']).intersection(set(p2d['camp_id'])))
            if not common_camps:
                st.error("Bu iki oyuncunun birlikte katıldığı ortak bir kamp bulunamadı.")
                st.stop()
                
            camp_dict = {row['camp_name']: row['camp_id'] for _, row in db_manager.get_camps().iterrows() if row['camp_id'] in common_camps}
            sc = st.selectbox("ORTAK KAMP SEÇİMİ", list(camp_dict.keys()), key="cmp_camp")
            sid = camp_dict[sc]
            
            p1d = p1d[p1d['camp_id'] == sid]
            p2d = p2d[p2d['camp_id'] == sid]
            t1d = t1d[t1d['camp_id'] == sid]
            t2d = t2d[t2d['camp_id'] == sid]

        if ses != "Tümü":
            p1d = p1d[p1d['tip'].str.upper() == ses]
            p2d = p2d[p2d['tip'].str.upper() == ses]
            t1d = t1d[t1d['tip'].str.upper() == ses]
            t2d = t2d[t2d['tip'].str.upper() == ses]

        if p1d.empty or p2d.empty:
            st.warning("Seçilen filtreler doğrultusunda karşılaştırılabilecek ortak veri bulunamadı."); st.stop()

        # Skor Hesaplamaları (Her oyuncu kendi yaş grubunun takımına göre skorlanır)
        s1 = calculate_composite_score(p1d, t1d)
        s2 = calculate_composite_score(p2d, t2d)

        # Görsel Profil Kartları
        p1_info = db_manager.get_player_info(p1)
        p2_info = db_manager.get_player_info(p2)
        p1_img = p1_info.get('photo_url') or "https://cdn-icons-png.flaticon.com/512/847/847969.png"
        p2_img = p2_info.get('photo_url') or "https://cdn-icons-png.flaticon.com/512/847/847969.png"

        L, M, R = st.columns([5, 1, 5])
        def _player_box(name, age, color, score, img_url):
            c = percentile_color(score.get('composite', 50))
            bg = '#fff0f0' if color == COLORS['GREEN'] else '#f5f5f5'
            return f"""
            <div style="background:linear-gradient(135deg,{bg},white); border:2px solid {color}; border-radius:16px; padding:20px; text-align:center; position:relative; box-shadow:0 4px 10px rgba(0,0,0,0.05);">
                <img src="{img_url}" style="width:100px; height:100px; border-radius:50%; object-fit:cover; border:3px solid {color}; margin-bottom:10px; background:white;">
                <div style="font-family:'Bebas Neue',sans-serif;font-size:26px; letter-spacing:1.5px; color:{color}; line-height:1;">{name.upper()}</div>
                <div style="font-size:12px; font-weight:bold; color:#4B5563; margin-top:4px;">{age} Takımı Skoru</div>
                <div style="font-family:'Bebas Neue',sans-serif;font-size:44px;color:{c};line-height:1; margin-top:5px;">
                    {score.get('composite',0):.0f}%
                </div>
            </div>"""

        with L:
            st.markdown(_player_box(p1, age1, COLORS['GREEN'], s1, p1_img), unsafe_allow_html=True)
            st.write("")
            c_L1, c_L2 = st.columns(2)
            with c_L1: st.markdown(f"<div class='metric-card' style='padding:10px;'><div class='sc-label'>GEÇERLİ SEANS</div><div class='sc-val' style='font-size:22px;'>{len(p1d)}</div></div>", unsafe_allow_html=True)
            with c_L2: st.markdown(f"<div class='metric-card' style='padding:10px;'><div class='sc-label'>ORT. MESAFE</div><div class='sc-val' style='font-size:22px;'>{p1d['total_distance'].mean():.0f} <span style='font-size:10px;color:#9CA3AF;'>m</span></div></div>", unsafe_allow_html=True)

        with M:
            st.markdown("<div style='text-align:center;padding-top:70px;font-family:\"Bebas Neue\",sans-serif; font-size:42px;font-weight:900;color:#D1D5DB;letter-spacing:2px;'>VS</div>", unsafe_allow_html=True)

        with R:
            st.markdown(_player_box(p2, age2, COLORS['BLACK'], s2, p2_img), unsafe_allow_html=True)
            st.write("")
            c_R1, c_R2 = st.columns(2)
            with c_R1: st.markdown(f"<div class='metric-card' style='padding:10px;'><div class='sc-label'>GEÇERLİ SEANS</div><div class='sc-val' style='font-size:22px;'>{len(p2d)}</div></div>", unsafe_allow_html=True)
            with c_R2: st.markdown(f"<div class='metric-card' style='padding:10px;'><div class='sc-label'>ORT. MESAFE</div><div class='sc-val' style='font-size:22px;'>{p2d['total_distance'].mean():.0f} <span style='font-size:10px;color:#9CA3AF;'>m</span></div></div>", unsafe_allow_html=True)

        st.divider()

        # AÇIKLAMA: Kıyaslamalı Percentile Bar Grafiği
        section_title("SKORLAMA (PERCENTILE) KARŞILAŞTIRMASI", "📊")
        info_box("Aşağıdaki grafik, oyuncuların kendi yaş gruplarındaki takımlara göre aldıkları Atletik Skorları (Percentile) karşılaştırır. Yüzde (%50) çizgisi takım medyanını (ortasını) temsil eder.")
        
        pct_m = [m for m in PRIMARY_METRICS if m in p1d.columns and m in p2d.columns
                 and p1d[m].dropna().any() and p2d[m].dropna().any()]
        labels = [METRICS.get(m,{}).get('display',m).upper() for m in pct_m]
        v1 = [s1.get(m, 50) for m in pct_m]
        v2 = [s2.get(m, 50) for m in pct_m]

        fig_pct = go.Figure()
        fig_pct.add_trace(go.Bar(
            name=p1.upper(), x=labels, y=v1,
            marker=dict(color=COLORS['GREEN'], opacity=0.9),
            text=[f"%{v:.0f}" for v in v1], textposition='outside',
            textfont=dict(family='DM Sans', size=11, weight='bold'),
        ))
        fig_pct.add_trace(go.Bar(
            name=p2.upper(), x=labels, y=v2,
            marker=dict(color=COLORS['BLACK'], opacity=0.9),
            text=[f"%{v:.0f}" for v in v2], textposition='outside',
            textfont=dict(family='DM Sans', size=11, weight='bold'),
        ))
        fig_pct.add_hline(y=50, line_dash='dash', line_color=COLORS['GRAY_500'],
                           annotation_text="TAKIM MEDYANI",
                           annotation_font=dict(size=10, color=COLORS['GRAY_600'], weight='bold'))
        fig_pct.update_layout(
            barmode='group', height=450,
            xaxis=dict(tickangle=-20, tickfont=dict(family='DM Sans', size=11, weight='bold')),
            yaxis=dict(title='Skor (%)', range=[0, 120], gridcolor='#F3F4F6'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(weight='bold')),
            plot_bgcolor='#FAFAFA', paper_bgcolor=COLORS['WHITE'],
            margin=dict(t=40),
        )
        st.plotly_chart(fig_pct, width='stretch')

        st.divider()
        section_title("GÖRSEL METRİK KARŞILAŞTIRMASI", "📈")
        avail = [m for m in PRIMARY_METRICS if m in p1d.columns and
                 p1d[m].notna().any() and p2d[m].notna().any()]
        cols = st.columns(2)
        for idx, metric in enumerate(avail):
            with cols[idx % 2]:
                combined_team = pd.concat([t1d, t2d]) if show_team else None
                fig = plot_player_comparison(p1d, p2d, metric, combined_team, p1, p2)
                st.plotly_chart(fig, width='stretch')

        st.divider()
        # ── YENİ EKLENEN ÖZELLİK: OYUNCU H2H FARK TABLOSU YÜZDELİKLİ ───────────
        section_title("DETAYLI İSTATİSTİK VE FARK ANALİZİ", "📋", tooltip="Oyuncu 1'in Oyuncu 2'ye göre yüzde kaç avantajlı veya dezavantajlı olduğunu gösterir.")
        
        rows = []
        for m in avail:
            p1v = p1d[m].mean()
            p2v = p2d[m].mean()
            mi  = METRICS.get(m, {})
            
            # Fark Hesabı (P1'in P2'ye göre yüzdelik durumu)
            if p2v != 0 and not pd.isna(p1v) and not pd.isna(p2v):
                diff_pct = ((p1v - p2v) / p2v) * 100
                if diff_pct > 0:
                    fark_html = f"<span style='color:{COLORS['SUCCESS']}; font-weight:bold;'>🟢 +%{diff_pct:.1f}</span>"
                elif diff_pct < 0:
                    fark_html = f"<span style='color:{COLORS['DANGER']}; font-weight:bold;'>🔴 -%{abs(diff_pct):.1f}</span>"
                else:
                    fark_html = f"<span style='color:{COLORS['GRAY_500']}; font-weight:bold;'>🔵 %0.0</span>"
            else:
                fark_html = "—"

            rows.append({
                'METRİK': mi.get('display', m).upper(), 
                'BİRİM': mi.get('unit',''),
                f"{p1.upper()} (ORT)": f"{p1v:.1f}",
                f"{p2.upper()} (ORT)": f"{p2v:.1f}",
                'FARK (%)': fark_html # Yeni % Fark Kolonu
            })
            
        df_tbl = pd.DataFrame(rows)
        # Markdown destekli (renkli ikonlar için) tablo basımı
        st.markdown(df_tbl.to_html(escape=False, index=False, classes="table table-striped", justify="center"), unsafe_allow_html=True)
        # Excel'e atarken html etiketlerini temizleyip atıyoruz
        export_df = df_tbl.copy()
        export_df['FARK (%)'] = export_df['FARK (%)'].str.replace(r'<[^>]*>', '', regex=True)
        render_export_buttons(df=export_df, key_prefix="cmp_tbl", filename=f"h2h_{p1}_vs_{p2}")

    # ════════════════════════════════════════════════════════════════════════
    # MODÜL 2: KAMP KARŞILAŞTIRMA
    # ════════════════════════════════════════════════════════════════════════
    elif cmp_type == "🔁 KAMP KARŞILAŞTIRMA":
        age_group = st.selectbox("YAŞ GRUBU SEÇİN", AGE_GROUPS, key="kc_age")
        raw_age_data = db_manager.get_data_by_age_group(age_group)
        age_data = apply_minute_filter(raw_age_data)
        
        camps_df = db_manager.get_camps(age_group)
        camp_options = {row['camp_name']: row['camp_id'] for _, row in camps_df.iterrows()}

        section_title("KAMP KARŞILAŞTIRMASI", "🔁")
        info_box("Aynı yaş grubuna ait iki farklı kampı seçerek takımın kamp bazındaki gelişimini veya düşüşünü (Trend) % Fark oranıyla karşılaştırın.")

        if len(camp_options) < 2:
            st.warning("Karşılaştırma için bu yaş grubunda en az 2 kamp gerekli."); st.stop()

        k1, k2, k3 = st.columns(3)
        with k1: camp1_name = st.selectbox("1. KAMP", list(camp_options.keys()), key="kc_k1")
        with k2: camp2_name = st.selectbox("2. KAMP", list(camp_options.keys()), index=min(1, len(camp_options)-1), key="kc_k2")
        with k3: ses = st.radio("SEANS TİPİ", ["Tümü","TRAINING","MATCH"], horizontal=True, key="kc_ses")

        if camp1_name == camp2_name:
            st.warning("Farklı iki kamp seçin."); st.stop()

        c1_id = camp_options[camp1_name]
        c2_id = camp_options[camp2_name]
        
        c1d_raw = db_manager.get_data_by_camp(c1_id)
        c2d_raw = db_manager.get_data_by_camp(c2_id)
        
        c1d = apply_minute_filter(c1d_raw)
        c2d = apply_minute_filter(c2d_raw)

        if ses != "Tümü":
            c1d = c1d[c1d['tip'].str.upper() == ses]
            c2d = c2d[c2d['tip'].str.upper() == ses]

        kk1, kk2 = st.columns(2)
        with kk1:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#fff0f0,white); border:2px solid {COLORS['GREEN']};border-radius:16px; padding:25px;text-align:center; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
                <div style="font-family:'Bebas Neue',sans-serif;font-size:26px; letter-spacing:2px;color:{COLORS['GREEN']};">
                    🔴 {camp1_name.upper()}
                </div>
                <div style="font-size:14px;color:{COLORS['GRAY_700']};margin-top:10px; font-weight:bold;">
                    {c1d['player_name'].nunique()} OYUNCU &nbsp;·&nbsp; {c1d['tarih'].nunique()} GÜN
                </div>
            </div>""", unsafe_allow_html=True)
        with kk2:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#f5f5f5,white); border:2px solid {COLORS['BLACK']};border-radius:16px; padding:25px;text-align:center; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
                <div style="font-family:'Bebas Neue',sans-serif;font-size:26px; letter-spacing:2px;color:{COLORS['BLACK']};">
                    ⚫ {camp2_name.upper()}
                </div>
                <div style="font-size:14px;color:{COLORS['GRAY_700']};margin-top:10px; font-weight:bold;">
                    {c2d['player_name'].nunique()} OYUNCU &nbsp;·&nbsp; {c2d['tarih'].nunique()} GÜN
                </div>
            </div>""", unsafe_allow_html=True)

        st.divider()

        kc_avail = [m for m in PRIMARY_METRICS if m in c1d.columns and m in c2d.columns
                    and c1d[m].dropna().any() and c2d[m].dropna().any()]
        
        kc_metric = st.selectbox("GRAFİK İÇİN METRİK SEÇİMİ", kc_avail,
                                  format_func=lambda x: METRICS.get(x,{}).get('display',x).upper(),
                                  key="kc_metric")

        fig_kc = plot_camp_comparison(c1d, c2d, kc_metric, camp1_name, camp2_name)
        st.plotly_chart(fig_kc, width='stretch')

        # ── YENİ EKLENEN ÖZELLİK: KAMP % FARK TABLOSU ───────────────────────────
        section_title("KAMP ÖZET VE % FARK TABLOSU", "📋")
        avail_m_kc = [m for m in PRIMARY_METRICS if m in c1d.columns and c1d[m].dropna().any()]
        rows = []
        for m in avail_m_kc:
            mi = METRICS.get(m, {'display':m, 'unit':''})
            v1 = c1d[m].mean(); v2 = c2d[m].mean()
            
            # Fark ve Yüzdelik Değişim (Kamp 2'nin Kamp 1'e göre durumu)
            if not pd.isna(v1) and not pd.isna(v2) and v1 != 0:
                diff_val = v2 - v1
                diff_pct = (diff_val / v1) * 100
                
                if diff_pct > 0:
                    diff_html = f"<span style='color:{COLORS['SUCCESS']}; font-weight:bold;'>🟢 +%{diff_pct:.1f}</span>"
                elif diff_pct < 0:
                    diff_html = f"<span style='color:{COLORS['DANGER']}; font-weight:bold;'>🔴 -%{abs(diff_pct):.1f}</span>"
                else:
                    diff_html = f"<span style='color:{COLORS['GRAY_500']}; font-weight:bold;'>🔵 %0.0</span>"
            else:
                diff_html = "—"

            rows.append({
                'METRİK':       mi['display'].upper(),
                'BİRİM':        mi['unit'],
                camp1_name.upper(): f"{v1:.2f}" if not pd.isna(v1) else '—',
                camp2_name.upper(): f"{v2:.2f}" if not pd.isna(v2) else '—',
                '% FARK':       diff_html
            })
            
        kc_df = pd.DataFrame(rows)
        # Markdown ile renkli HTML tablo
        st.markdown(kc_df.to_html(escape=False, index=False, classes="table table-striped", justify="center"), unsafe_allow_html=True)
        
        export_df = kc_df.copy()
        export_df['% FARK'] = export_df['% FARK'].str.replace(r'<[^>]*>', '', regex=True)
        render_export_buttons(fig=fig_kc, df=export_df, key_prefix="kc", filename=f"kamp_{camp1_name}_vs_{camp2_name}")

    # ════════════════════════════════════════════════════════════════════════
    # MODÜL 3: ÇOKLU RADAR
    # ════════════════════════════════════════════════════════════════════════
    else:
        age_group = st.selectbox("YAŞ GRUBU SEÇİN", AGE_GROUPS, key="mr_age")
        raw_age_data = db_manager.get_data_by_age_group(age_group)
        age_data = apply_minute_filter(raw_age_data)
        players = db_manager.get_players(age_group)
        
        camps_df = db_manager.get_camps(age_group)
        camp_options = {row['camp_name']: row['camp_id'] for _, row in camps_df.iterrows()}

        section_title("ÇOKLU OYUNCU RADAR ANALİZİ", "⚔️")
        info_box("Aynı yaş grubundaki 2 ile 6 arasındaki oyuncuyu aynı radar düzlemine yerleştirerek oyun profillerini kıyaslayın.")
        
        sel_players = st.multiselect(
            "OYUNCULAR (2–6 Seçim Yapabilirsiniz)", players,
            default=players[:min(2, len(players))] if players else [], key="cmp_multi"
        )
        if len(sel_players) < 2:
            st.warning("En az 2 oyuncu seçin."); st.stop()
        if len(sel_players) > 6:
            st.warning("Grafiğin anlaşılabilir olması için en fazla 6 oyuncu seçebilirsiniz."); st.stop()

        r1, r2 = st.columns(2)
        with r1: ses = st.radio("SEANS TİPİ", ["Tümü","TRAINING","MATCH"], horizontal=True, key="cmp_rses")
        with r2: camp_filter_r = st.checkbox("Belirli bir kampa sınırla", key="cmp_rcf")

        td = age_data if ses == "Tümü" else age_data[age_data['tip'].str.upper() == ses]

        if camp_filter_r and camp_options:
            rsc = st.selectbox("KAMP SEÇİMİ", list(camp_options.keys()), key="cmp_rcamp")
            rsid = camp_options[rsc]
            td = td[td['camp_id'] == rsid]

        pd_dict = {}
        for p in sel_players:
            pdata_raw = db_manager.get_data_by_player(p)
            pdata = apply_minute_filter(pdata_raw)
            if ses != "Tümü":
                pdata = pdata[pdata['tip'].str.upper() == ses]
            if camp_filter_r and camp_options:
                pdata = pdata[pdata['camp_id'] == rsid]
            pd_dict[p] = pdata

        if td.empty:
            st.warning("Seçilen filtreler için takım verisi yok."); st.stop()

        fig_r = plot_radar_comparison_multiple(pd_dict, td)
        st.plotly_chart(fig_r, width='stretch')
        render_export_buttons(fig=fig_r, key_prefix="cmp_radar", filename="radar_karsilastirma")

        st.markdown("""
        <div style="text-align:center;font-size:12px;color:#9CA3AF;margin-top:8px; font-weight:bold;">
            📌 İndeks = (Oyuncu Ort. / Takım Max) × 100 &nbsp;|&nbsp; Merkezden uzaklaştıkça performans artar.
        </div>""", unsafe_allow_html=True)

        st.divider()
        section_title("ÇOKLU PERCENTILE (SKOR) TABLOSU", "📊")
        pct_rows = []
        for p in sel_players:
            pdata = pd_dict[p]
            sc = calculate_composite_score(pdata, td)
            row = {'OYUNCU': p.upper()}
            for m in PRIMARY_METRICS:
                if m in pdata.columns and pdata[m].dropna().any():
                    mi = METRICS.get(m, {})
                    row[mi.get('display', m).upper()] = f"%{sc.get(m, 50):.0f}"
            row['BİLEŞİK SKOR'] = f"%{sc.get('composite', 50):.0f}"
            pct_rows.append(row)
        pct_df = pd.DataFrame(pct_rows)
        st.dataframe(pct_df, width='stretch', hide_index=True)
        render_export_buttons(df=pct_df, key_prefix="cmp_ptbl", filename="coklu_percentile")

        st.divider()
        section_title("DETAYLI METRİK TABLOSU", "📋")
        avail = [m for m in PRIMARY_METRICS if m in td.columns and td[m].notna().any()]
        rows = []
        for p in sel_players:
            pdata = pd_dict[p]
            for m in avail:
                pv = pdata[m].mean() if pdata[m].notna().any() else 0
                tv = td[m].mean()    if td[m].notna().any()    else 0
                rows.append({
                    'OYUNCU': p.upper(),
                    'METRİK': METRICS.get(m,{}).get('display',m).upper(),
                    'OYUNCU ORT.': f"{pv:.1f}",
                    'TAKIM ORT.':  f"{tv:.1f}",
                    'PERFORMANS İNDEKSİ': f"%{pv/tv*100:.0f}" if tv>0 else '—',
                })
        tbl = pd.DataFrame(rows)
        st.dataframe(tbl, width='stretch', hide_index=True)
        render_export_buttons(df=tbl, key_prefix="cmp_mtbl", filename="coklu_karsilastirma")

except Exception as e:
    st.error(f"❌ Hata: {str(e)}")
    import traceback; st.code(traceback.format_exc())

st.markdown('<div class="tff-footer"><p>Rugby Performans Sistemi · Karşılaştırma Analizi</p></div>', unsafe_allow_html=True)