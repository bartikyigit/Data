import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from config import AGE_GROUPS, METRICS, PRIMARY_METRICS, DEFAULT_MINUTES
from database import db_manager
from styles import inject_styles, page_header, section_title, info_box, COLORS, PLAYER_PALETTE
from utils import render_export_buttons, calculate_composite_score

# ── SAYFA AYARLARI VE ANALİTİK GİRİŞ ──────────────────────────────────────────
st.set_page_config(page_title="Scatter Analizi | TFF", layout="wide")
inject_styles()
page_header("🎯", "SCATTER VE KORELASYON LABORATUVARI",
            "Metrik İlişkileri · Oyuncu Tipolojileri · Dörtlü Bölge (Quadrant) Analizi")

# 📝 ANALİZ NOTU: İstatistiksel İlişki ve Quadrant Analizi
info_box("""
<b>SCATTER ANALİZİ VE KORELASYON METODOLOJİSİ:</b><br>
Bu laboratuvar, iki atletik metrik arasındaki ilişkiyi inceler. Ekranda oluşan dört ana bölge (Quadrant), 
popülasyonun medyanına (ortalamasına) göre <b>'Performans Tipolojisi'</b> sınıflaması yapmanızı sağlar.<br>
Örneğin; X eksenine 'Sürat', Y eksenine 'Mesafe' koyduğunuzda hem hızlı hem dayanıklı olan <b>'Elit Atletleri'</b> sağ üst köşede görebilirsiniz.
""")

# ── 1. VERİ KÜMESİ AYARLARI VE FİLTRELER ──────────────────────────────────────
section_title("VERİ KÜMESİ AYARLARI", "⚙️")
f1, f2, f3 = st.columns(3)
with f1:
    age_group = st.selectbox("HEDEF YAŞ GRUBU", AGE_GROUPS, key="sc_age")

raw_age_data = db_manager.get_data_by_age_group(age_group)
if raw_age_data.empty:
    st.warning(f"{age_group} için veri bulunamadı."); st.stop()

camps_df = db_manager.get_camps(age_group)
camp_options = {"Tüm Kamplar": None}
camp_options.update({row['camp_name']: row['camp_id'] for _, row in camps_df.iterrows()})

with f2:
    sel_camp = st.selectbox("KAMP SEÇİMİ", list(camp_options.keys()), key="sc_camp")
with f3:
    ses = st.multiselect("SEANS TİPİ", ['TRAINING', 'MATCH'], default=['TRAINING', 'MATCH'], key="sc_ses")

# ── VERİ TEMİZLİĞİ: İSTATİSTİKSEL ARINDIRMA (DATA CLEANING) ──────────────────
with st.expander("⚙️ VERİ ZIRHI: DAKİKA VE FİZİKSEL EŞİKLER", expanded=False):
    st.markdown("<div style='font-size:13px; color:#4B5563; margin-bottom:10px;'>Grafikteki sapmaları ve yanlış kümelenmeleri önlemek için az süre alınan seansları filtreleyin.</div>", unsafe_allow_html=True)
    dk1, dk2 = st.columns(2)
    with dk1: min_train_dk = st.number_input("Minimum Antrenman Dakikası", value=DEFAULT_MINUTES['TRAINING'], step=5, key="sc_dk_tr")
    with dk2: min_match_dk = st.number_input("Minimum Maç Dakikası", value=DEFAULT_MINUTES['MATCH'], step=5, key="sc_dk_ma")

def apply_minute_filter(df):
    if df.empty: return df
    is_tr = df['tip'].str.upper().str.contains('TRAINING')
    is_ma = df['tip'].str.upper().str.contains('MATCH')
    mask = (is_tr & (df['minutes'] >= min_train_dk)) | (is_ma & (df['minutes'] >= min_match_dk))
    return df[mask].copy()

# Filtreleri Uygula
data_filtered = raw_age_data.copy()
if camp_options[sel_camp] is not None:
    data_filtered = data_filtered[data_filtered['camp_id'] == camp_options[sel_camp]]
if ses:
    data_filtered = data_filtered[data_filtered['tip'].isin(ses)]

data = apply_minute_filter(data_filtered)

if data.empty:
    st.warning("Seçilen filtrelerde veri seti bulunamadı. Lütfen filtreleri esnetin."); st.stop()

st.divider()

# ── 2. EKSEN VE GÖRSEL AYARLARI ────────────────────────────────────────────────
section_title("ANALİTİK GÖRSELLEŞTİRME AYARLARI", "🎨")

avail_m = [m for m in PRIMARY_METRICS if m in data.columns and data[m].dropna().any()]

e1, e2, e3, e4 = st.columns(4)
with e1:
    x_metric = st.selectbox("X EKSENİ (Yatay)", avail_m, format_func=lambda x: METRICS.get(x, {}).get('display', x).upper(), key="sc_x")
with e2:
    y_default_idx = min(avail_m.index(x_metric) + 1, len(avail_m) - 1) if x_metric in avail_m else 0
    y_metric = st.selectbox("Y EKSENİ (Dikey)", avail_m, index=y_default_idx, format_func=lambda x: METRICS.get(x, {}).get('display', x).upper(), key="sc_y")
with e3:
    color_by = st.radio("RENK KODLAMA", ["Oyuncu Bazlı", "Seans Tipi Bazlı"], horizontal=True, key="sc_color")
with e4:
    agg_mode = st.radio("VERİ YOĞUNLUĞU", ["Ham Veri", "Ortalama Veri"], horizontal=True, key="sc_agg")

# AÇIKLAMA: Harita üzerinde kalabalığı önlemek için özel etiketleme sistemi.
players_in_data = sorted(data['player_name'].unique())
st.markdown("<b>HARİTADA İSİMLERİ GÖSTERİLECEK OYUNCULAR (Custom Labeling)</b>", unsafe_allow_html=True)
show_labels_for = st.multiselect("", players_in_data, key="sc_labels", help="Görsel karmaşayı önlemek için sadece seçilenlerin isimleri basılır.")
show_avg = st.checkbox("Grup Ortalamalarını ve Dörtlü Bölgeleri Göster (Quadrant)", value=True, key="sc_avg")

if agg_mode == "Ortalama Veri":
    plot_data = data.groupby('player_name')[[x_metric, y_metric, 'tip']].agg({x_metric: 'mean', y_metric: 'mean', 'tip': 'first'}).reset_index()
else:
    plot_data = data.copy()

# ── SCATTER PLOT ÇIZIM MOTORU ─────────────────────────────────────────────────
st.divider()
x_label, y_label = METRICS.get(x_metric, {}).get('display', x_metric).upper(), METRICS.get(y_metric, {}).get('display', y_metric).upper()
x_unit, y_unit = METRICS.get(x_metric, {}).get('unit', ''), METRICS.get(y_metric, {}).get('unit', '')

fig = go.Figure()

if color_by == "Seans Tipi Bazlı":
    for tip, clr, sym in [('TRAINING', COLORS['BLACK'], 'circle'), ('MATCH', COLORS['RED'], 'hexagram')]:
        df_tip = plot_data[plot_data['tip'].str.upper().str.contains(tip)]
        if df_tip.empty: continue
        text_list = [name.upper() if name in show_labels_for else "" for name in df_tip['player_name']]
        fig.add_trace(go.Scatter(x=df_tip[x_metric], y=df_tip[y_metric], mode='markers+text' if any(text_list) else 'markers', name=tip, text=text_list, textposition="top center",
                                 marker=dict(color=clr, size=12, opacity=0.7, line=dict(width=1, color='white'), symbol=sym), customdata=df_tip['player_name'],
                                 hovertemplate="<b>%{customdata}</b><br>"+f"{x_label}: %{{x:.1f}} {x_unit}<br>{y_label}: %{{y:.1f}} {y_unit}<extra></extra>"))
else:
    for i, p_name in enumerate(players_in_data):
        df_p = plot_data[plot_data['player_name'] == p_name]
        if df_p.empty: continue
        is_sel = p_name in show_labels_for
        fig.add_trace(go.Scatter(x=df_p[x_metric], y=df_p[y_metric], mode='markers+text' if is_sel else 'markers', name=p_name.upper(), text=[p_name.upper() if is_sel else ""] * len(df_p),
                                 textposition="top center", marker=dict(color=PLAYER_PALETTE[i % len(PLAYER_PALETTE)], size=11, opacity=0.85 if is_sel else 0.5, line=dict(width=1, color='white')),
                                 hovertemplate="<b>"+p_name.upper()+"</b><br>"+f"{x_label}: %{{x:.1f}}<br>{y_label}: %{{y:.1f}}<extra></extra>"))

if show_avg:
    xa, ya = plot_data[x_metric].mean(), plot_data[y_metric].mean()
    fig.add_vline(x=xa, line_dash="dash", line_color=COLORS['GRAY_500'], line_width=1.5)
    fig.add_hline(y=ya, line_dash="dash", line_color=COLORS['GRAY_500'], line_width=1.5)
    fig.add_annotation(x=plot_data[x_metric].max(), y=plot_data[y_metric].max(), text="ELİT BÖLGE", showarrow=False, font=dict(color=COLORS['SUCCESS'], size=10, weight='bold'), xanchor="right")
    fig.add_annotation(x=plot_data[x_metric].min(), y=plot_data[y_metric].min(), text="GELİŞİM BÖLGESİ", showarrow=False, font=dict(color=COLORS['DANGER'], size=10, weight='bold'), xanchor="left")

fig.update_layout(title=dict(text=f"<b>{x_label} VS {y_label} DAĞILIM MATRİSİ</b>", font=dict(family='Bebas Neue', size=24)),
                  xaxis=dict(title=f"{x_label} ({x_unit})", gridcolor='#F3F4F6'), yaxis=dict(title=f"{y_label} ({y_unit})", gridcolor='#F3F4F6'),
                  template='plotly_white', height=650, plot_bgcolor='#FAFAFA', margin=dict(t=80))

st.plotly_chart(fig, use_container_width=True)

# ── İSTATİSTİKSEL ÖZET PANELİ ─────────────────────────────────────────────────
x_valid = plot_data[x_metric].replace(0, pd.NA).dropna()
y_valid = plot_data[y_metric].replace(0, pd.NA).dropna()

# Korelasyon Katsayısı (Pearson)
if len(plot_data) > 2:
    corr = plot_data[[x_metric, y_metric]].corr().iloc[0, 1]
    corr_desc = "Güçlü Pozitif" if corr > 0.7 else ("Orta" if corr > 0.4 else "Zayıf / İlişkisiz")
else:
    corr, corr_desc = 0.0, "Yetersiz Veri"

info_box(f"📈 <b>KORELASYON:</b> {corr:.2f} ({corr_desc}) &nbsp;|&nbsp; <b>GÖZLEM:</b> {len(plot_data)} <br> <b>{x_label} ORT:</b> {plot_data[x_metric].mean():.1f} &nbsp;|&nbsp; <b>{y_label} ORT:</b> {plot_data[y_metric].mean():.1f}")
render_export_buttons(fig=fig, df=plot_data.round(2), key_prefix="sc", filename=f"scatter_{x_metric}_vs_{y_metric}")

# ── 3. ÖZEL OYUNCU KİMLİK KARTI (TEK OYUNCU SEÇİLİRSE) ─────────────────────────
if len(show_labels_for) == 1:
    st.divider()
    sel_p = show_labels_for[0]
    section_title(f"DETAYLI PROFiL: {sel_p.upper()}", "👤")
    
    with st.expander("📄 ATLETİK KİMLİK ÖZETİ", expanded=True):
        p1, p2 = st.columns([1, 2])
        with p1:
            st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
            st.image("https://img.uefa.com/imgfiles/v3/players/250106207.png", caption=sel_p.upper(), width=180)
            st.markdown("</div>", unsafe_allow_html=True)
            
            p_score = calculate_composite_score(data[data['player_name']==sel_p], data)
            st.markdown(f"""
            <div style='background:#F9FAFB; padding:15px; border-left:5px solid #E30A17; margin-top:10px;'>
                <div style='font-size:12px; color:#6B7280; font-weight:bold;'>BİLEŞİK SKOR (Percentile)</div>
                <div style='font-size:36px; color:#E30A17; font-weight:bold; font-family:"Bebas Neue", sans-serif;'>%{p_score.get('composite', 0):.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        with p2:
            radar_m = [m for m in PRIMARY_METRICS if m in data.columns][:7]
            if radar_m:
                labels = [METRICS.get(m,{}).get('display',m).upper() for m in radar_m]
                vals = [p_score.get(m, 50) for m in radar_m]
                fig_r = go.Figure()
                fig_r.add_trace(go.Scatterpolar(r=vals + [vals[0]], theta=labels + [labels[0]], fill='toself', name="Oyuncu", line_color=COLORS['RED']))
                fig_r.add_trace(go.Scatterpolar(r=[50]*len(vals) + [50], theta=labels + [labels[0]], mode='lines', name="Takım Medyanı", line=dict(color=COLORS['GRAY_500'], dash='dash')))
                fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 110])), height=400, title="<b>ATLETİK GAP ANALİZİ</b>", margin=dict(t=50, b=20))
                st.plotly_chart(fig_r, use_container_width=True)

# ── 4. YENİ GERÇEKÇİ ANALİZ: TAKIM TİPOLOJİSİ VE KADRO MÜHENDİSLİĞİ ───────────
# AÇIKLAMA: Karmaşık Matris analizi yerine, antrenörlerin doğrudan aksiyon alabileceği 
# "Kadro Mühendisliği (Squad Engineering)" sınıflandırması eklenmiştir. Scatter plot 
# üzerindeki X ve Y ekseni ortalamalarına göre oyuncuları 4 gruba ayırır.
st.divider()
st.divider()
with st.expander("🧠 KADRO MÜHENDİSLİĞİ VE TİPOLOJİ SINIFLANDIRMASI (Quadrant Analysis)", expanded=False):
    section_title("TAKIM TİPOLOJİSİ (ROL DAĞILIMI)", "🧠")
    st.markdown(f"Yukarıdaki grafikte yer alan **Takım Ortalamaları ({x_label} ve {y_label})** baz alınarak oyuncuların fiziksel rolleri otomatik olarak tespit edilir. Antrenörler bu tabloyu kullanarak antrenman gruplarını (Örn: Ekstra koşu yapacaklar vs. Dinlenecekler) ayırabilir.")
    
    # Ortalamaları hesapla
    x_mean = plot_data[x_metric].mean()
    y_mean = plot_data[y_metric].mean()
    
    # Oyuncuları 4 bölgeye (Quadrant) göre sınıflandıran fonksiyon
    def classify_player(row):
        if pd.isna(row[x_metric]) or pd.isna(row[y_metric]):
            return "Veri Eksik"
        if row[x_metric] >= x_mean and row[y_metric] >= y_mean:
            return "🌟 ÇİFT YÖNLÜ ELİT (Her İki Metrik Yüksek)"
        elif row[x_metric] >= x_mean and row[y_metric] < y_mean:
            return f"⚡ {x_label} DOMİNANT (Sadece X Yüksek)"
        elif row[x_metric] < x_mean and row[y_metric] >= y_mean:
            return f"🔋 {y_label} DOMİNANT (Sadece Y Yüksek)"
        else:
            return "📈 GELİŞİM BÖLGESİ (Her İki Metrik Düşük)"
            
    # Analiz tablosunu oluştur
    plot_data['Fiziksel Tipoloji'] = plot_data.apply(classify_player, axis=1)
    
    c1, c2 = st.columns([1, 2])
    with c1:
        # Hangi profilden kaç oyuncu var? (Donut Chart)
        pie_data = plot_data['Fiziksel Tipoloji'].value_counts().reset_index()
        pie_data.columns = ['Fiziksel Tipoloji', 'Kişi Sayısı']
        
        color_map = {
            "🌟 ÇİFT YÖNLÜ ELİT (Her İki Metrik Yüksek)": COLORS['SUCCESS'],     # Yeşil
            f"⚡ {x_label} DOMİNANT (Sadece X Yüksek)": "#3B82F6",               # Mavi
            f"🔋 {y_label} DOMİNANT (Sadece Y Yüksek)": "#F59E0B",               # Turuncu
            "📈 GELİŞİM BÖLGESİ (Her İki Metrik Düşük)": COLORS['DANGER'],       # Kırmızı
            "Veri Eksik": COLORS['GRAY_300']
        }
        
        fig_pie = go.Figure(go.Pie(
            labels=pie_data['Fiziksel Tipoloji'], 
            values=pie_data['Kişi Sayısı'], 
            hole=0.6,
            marker=dict(colors=[color_map.get(t, COLORS['GRAY_500']) for t in pie_data['Fiziksel Tipoloji']]),
            textinfo='value+percent',
            textfont=dict(size=14, weight='bold', color='white')
        ))
        fig_pie.update_layout(
            title=dict(text="<b>KADRO DAĞILIMI</b>", font=dict(family='Bebas Neue', size=20)),
            margin=dict(t=40, b=10, l=10, r=10), 
            height=350,
            showlegend=False
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with c2:
        # Detaylı Sınıflandırma Tablosu
        show_typo = plot_data[['player_name', x_metric, y_metric, 'Fiziksel Tipoloji']].copy()
        show_typo.columns = ['OYUNCU ADI', f"{x_label} ({x_unit})", f"{y_label} ({y_unit})", 'ATLETİK PROFİL SINIFI']
        st.dataframe(show_typo, use_container_width=True, hide_index=True)
        
        render_export_buttons(df=show_typo, key_prefix="sc_typo", filename=f"kadro_muhendisligi_{x_metric}_{y_metric}")

# ── HAM VERİ TABLOSU ──────────────────────────────────────────────────────────
st.divider()
with st.expander("📋 VERİ MATRİSİNİ İNCELE"):
    disp = plot_data.copy()
    if 'tarih' in disp.columns:
        disp['tarih'] = pd.to_datetime(disp['tarih']).dt.strftime('%d.%m.%Y')
    
    # Başlıkları profesyonelleştir
    rename_cols = {'player_name': 'OYUNCU', 'tip': 'SEANS TİPİ', 'tarih': 'TARİH', x_metric: x_label, y_metric: y_label}
    disp = disp.rename(columns=rename_cols)
    
    # Sadece ilgili kolonları göster
    cols_to_show = [c for c in rename_cols.values() if c in disp.columns]
    st.dataframe(disp[cols_to_show].round(2), use_container_width=True, hide_index=True)

st.markdown('<div class="tff-footer"><p>Rugby Performans Sistemi · Performans Analiz Laboratuvarı</p></div>', unsafe_allow_html=True)