import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from database import db_manager
from config import AGE_GROUPS
from styles import inject_styles, page_header, section_title, info_box, COLORS

st.set_page_config(page_title="Performans ve Kuvvet Testleri | Rugby Analitik", layout="wide")
inject_styles()

page_header("🏋️‍♂️", "FİZİKSEL PERFORMANS LABORATUVARI", 
            "Bireysel Profil Raporu, Tekil Nokta Dağılımı, Değişken Analizi ve Sıralamalar")

# 📝 BİLGİLENDİRME KUTUSU (Metodoloji)
with st.expander("📌 TEST METODOLOJİSİ, RİSK ANALİZİ VE LEJANT REHBERİ", expanded=False):
    st.markdown("""
    **Bu Modül Neyi Ölçer?**
    1. **Bireysel Performans (Bullet Grafikleri):** * 🔴 **Kırmızı Bar:** Oyuncunun kendi test değeri.
       * ⬛ **Siyah Çizgi:** Takımın o testteki Ortalaması.
       * ⬜ **Gri Arka Plan (Range):** Takımın en düşük ve en yüksek değerleri arasındaki yayılım (güven) bandı.
    2. **Görünmez Metrikler (Literatür):** * **EUR (Eksantrik Kullanım):** CMJ / SJ. Sıçramadaki elastik enerjiyi ölçer.
       * **Göreceli Kuvvet:** (N/kg). Saf kuvvetin vücut ağırlığına oranıdır.
       * **Split Zamanları:** Sprintte ivmelenme kalitesini ölçer.
    3. **Asimetri (Sakatlık Riski):** Sağ ve sol bacak arasında kuvvet farkının **%10 - %15'in üzerinde olması**, kas yırtığı riskinin habercisidir. Sistem bu asimetriyi yönlü olarak sunar.
    """, unsafe_allow_html=True)

# ── 1. VERİ ÇEKME VE FİLTRELEME ──────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
with c1:
    age_group = st.selectbox("YAŞ GRUBU SEÇİN", AGE_GROUPS, key="test_age")

raw_test_data = db_manager.get_test_data(age_group=age_group)

if raw_test_data.empty:
    st.warning(f"Sistemde {age_group} için kaydedilmiş test verisi bulunmuyor. Lütfen önce Ana Sayfa'dan test Excel'inizi yükleyin.")
    st.stop()

# Sayısal kolonları güvenli hale getir
numeric_cols = ['bw_kg', 'height_cm', 'cmj_jump_cm', 'slj_jump_cm', 'slj_jump_l_cm', 'slj_jump_r_cm', 
                'sj_jump_cm', 'nordic_l_n', 'nordic_r_n', 'nordic_imbalance_pct', 'pull_l_n', 'pull_r_n', 
                'pull_imbalance_pct', 'squeeze_l_n', 'squeeze_r_n', 'squeeze_imbalance_pct', 
                'knee_ext_l_n', 'knee_ext_r_n', 'knee_ext_imbalance_pct', 'sprint_10m', 'sprint_20m', 'sprint_30m']

for c in numeric_cols:
    if c in raw_test_data.columns:
        raw_test_data[c] = pd.to_numeric(raw_test_data[c], errors='coerce')

# ── TÜRETİLMİŞ METRİKLER (DERIVED METRICS - LİTERATÜR) ──
if 'cmj_jump_cm' in raw_test_data.columns and 'sj_jump_cm' in raw_test_data.columns:
    raw_test_data['eur'] = np.where(raw_test_data['sj_jump_cm'] > 0, raw_test_data['cmj_jump_cm'] / raw_test_data['sj_jump_cm'], np.nan)

if 'bw_kg' in raw_test_data.columns:
    bw = raw_test_data['bw_kg']
    if 'nordic_l_n' in raw_test_data.columns and 'nordic_r_n' in raw_test_data.columns:
        raw_test_data['rel_nordic'] = np.where(bw > 0, ((raw_test_data['nordic_l_n'] + raw_test_data['nordic_r_n']) / 2) / bw, np.nan)
    if 'pull_l_n' in raw_test_data.columns and 'pull_r_n' in raw_test_data.columns:
        raw_test_data['rel_pull'] = np.where(bw > 0, ((raw_test_data['pull_l_n'] + raw_test_data['pull_r_n']) / 2) / bw, np.nan)
    if 'squeeze_l_n' in raw_test_data.columns and 'squeeze_r_n' in raw_test_data.columns:
        raw_test_data['rel_squeeze'] = np.where(bw > 0, ((raw_test_data['squeeze_l_n'] + raw_test_data['squeeze_r_n']) / 2) / bw, np.nan)
    if 'knee_ext_l_n' in raw_test_data.columns and 'knee_ext_r_n' in raw_test_data.columns:
        raw_test_data['rel_knee'] = np.where(bw > 0, ((raw_test_data['knee_ext_l_n'] + raw_test_data['knee_ext_r_n']) / 2) / bw, np.nan)

if 'sprint_10m' in raw_test_data.columns and 'sprint_20m' in raw_test_data.columns:
    raw_test_data['split_10_20'] = raw_test_data['sprint_20m'] - raw_test_data['sprint_10m']
if 'sprint_20m' in raw_test_data.columns and 'sprint_30m' in raw_test_data.columns:
    raw_test_data['split_20_30'] = raw_test_data['sprint_30m'] - raw_test_data['sprint_20m']

# ── AKILLI ASİMETRİ (YÖN) HESAPLAYICI ──
def calc_dir_imb(row, l_col, r_col):
    l = row.get(l_col); r = row.get(r_col)
    if pd.isna(l) or pd.isna(r) or (l==0 and r==0): return np.nan
    diff = r - l
    m = max(l, r)
    if m == 0: return 0
    return (diff / m) * 100

for test in ['nordic', 'pull', 'squeeze', 'knee_ext']:
    raw_test_data[f"{test}_dir_imb"] = raw_test_data.apply(lambda r: calc_dir_imb(r, f"{test}_l_n", f"{test}_r_n"), axis=1)

def parse_slj_asym(row):
    pct = str(row.get('slj_asym_pct', '')).strip().upper()
    if pd.notna(row.get('slj_jump_l_cm')) and pd.notna(row.get('slj_jump_r_cm')):
        return calc_dir_imb(row, 'slj_jump_l_cm', 'slj_jump_r_cm')
    if pct and pct != 'NAN':
        num = ''.join(c for c in pct if c.isdigit() or c == '.')
        if num:
            num = float(num)
            if 'L' in pct: return -num
            return num
    return np.nan
raw_test_data['slj_jump_dir_imb'] = raw_test_data.apply(parse_slj_asym, axis=1)

# Tarih Filtresi
available_dates = sorted(raw_test_data['tarih'].unique(), reverse=True)
with c2:
    selected_date = st.selectbox("TEST TARİHİ", ["Tüm Testler (En Güncel)"] + list(available_dates), key="test_date")

if selected_date != "Tüm Testler (En Güncel)":
    test_data = raw_test_data[raw_test_data['tarih'] == selected_date].copy()
else:
    test_data = raw_test_data.sort_values('tarih').groupby('player_name').tail(1).copy()

players_in_data = sorted(test_data['player_name'].unique())
with c3:
    search_player = st.selectbox("ODAKLANACAK OYUNCU (Vurgulama)", ["Seçilmedi"] + players_in_data, key="test_player")

# ── METRİK SÖZLÜĞÜ ──
available_metrics_info = {
    'cmj_jump_cm': {'name': 'CMJ Sıçrama', 'unit': 'cm', 'invert': False, 'group': 'jump'},
    'sj_jump_cm': {'name': 'SJ Sıçrama', 'unit': 'cm', 'invert': False, 'group': 'jump'},
    'eur': {'name': 'EUR İndeksi (CMJ/SJ)', 'unit': 'x', 'invert': False, 'group': 'jump'},
    'slj_jump_cm': {'name': 'SLJ Sıçrama', 'unit': 'cm', 'invert': False, 'group': 'jump_asym'},
    'slj_jump_l_cm': {'name': 'SLJ Sol Bacak', 'unit': 'cm', 'invert': False, 'group': 'jump_asym'},
    'slj_jump_r_cm': {'name': 'SLJ Sağ Bacak', 'unit': 'cm', 'invert': False, 'group': 'jump_asym'},
    
    'rel_nordic': {'name': 'Göreceli Nordic (N/kg)', 'unit': 'N/kg', 'invert': False, 'group': 'nordic'},
    'nordic_l_n': {'name': 'Nordic Sol', 'unit': 'N', 'invert': False, 'group': 'nordic'},
    'nordic_r_n': {'name': 'Nordic Sağ', 'unit': 'N', 'invert': False, 'group': 'nordic'},
    
    'rel_pull': {'name': 'Göreceli Pull (N/kg)', 'unit': 'N/kg', 'invert': False, 'group': 'pull'},
    'pull_l_n': {'name': 'Pull Sol', 'unit': 'N', 'invert': False, 'group': 'pull'},
    'pull_r_n': {'name': 'Pull Sağ', 'unit': 'N', 'invert': False, 'group': 'pull'},
    
    'rel_squeeze': {'name': 'Göreceli Squeeze (N/kg)', 'unit': 'N/kg', 'invert': False, 'group': 'squeeze'},
    'squeeze_l_n': {'name': 'Squeeze Sol', 'unit': 'N', 'invert': False, 'group': 'squeeze'},
    'squeeze_r_n': {'name': 'Squeeze Sağ', 'unit': 'N', 'invert': False, 'group': 'squeeze'},
    
    'rel_knee': {'name': 'Göreceli KneeExt (N/kg)', 'unit': 'N/kg', 'invert': False, 'group': 'knee'},
    'knee_ext_l_n': {'name': 'KneeExt Sol', 'unit': 'N', 'invert': False, 'group': 'knee'},
    'knee_ext_r_n': {'name': 'KneeExt Sağ', 'unit': 'N', 'invert': False, 'group': 'knee'},
    
    'sprint_10m': {'name': '10m Sprint', 'unit': 'sn', 'invert': True, 'group': 'speed'},
    'split_10_20': {'name': '10-20m Geçişi', 'unit': 'sn', 'invert': True, 'group': 'speed'},
    'sprint_20m': {'name': '20m Sprint', 'unit': 'sn', 'invert': True, 'group': 'speed'},
    'split_20_30': {'name': '20-30m Geçişi', 'unit': 'sn', 'invert': True, 'group': 'speed'},
    'sprint_30m': {'name': '30m Sprint', 'unit': 'sn', 'invert': True, 'group': 'speed'}
}

asym_metrics = {
    'slj_jump_dir_imb': {'name': 'SLJ Asimetri', 'group': 'jump_asym'},
    'nordic_dir_imb': {'name': 'Nordic Asimetri', 'group': 'nordic'},
    'pull_dir_imb': {'name': 'Pull Asimetri', 'group': 'pull'},
    'squeeze_dir_imb': {'name': 'Squeeze Asimetri', 'group': 'squeeze'},
    'knee_ext_dir_imb': {'name': 'KneeExt Asimetri', 'group': 'knee'}
}

# RADAR GRAFİĞİ KATEGORİ TANIMLAMALARI (6 Başlıklı ve Açıklamalı)
radar_categories_def = {
    'Hız ve İvmelenme': {'keys': ['sprint_10m', 'sprint_20m', 'sprint_30m', 'split_10_20', 'split_20_30'], 'desc': 'Sprint Süreleri ve Split Geçişleri'},
    'Dikey Patlayıcılık': {'keys': ['cmj_jump_cm', 'sj_jump_cm', 'eur'], 'desc': 'CMJ, SJ ve Elastikiyet (EUR)'},
    'Yatay Patlayıcılık': {'keys': ['slj_jump_cm', 'slj_jump_l_cm', 'slj_jump_r_cm'], 'desc': 'Çift ve Tek Bacak SLJ'},
    'Arka Adale (Hamstring)': {'keys': ['nordic_l_n', 'nordic_r_n', 'rel_nordic'], 'desc': 'Nordic Max ve Göreceli Kuvvet'},
    'İç/Dış Bacak Kuvveti': {'keys': ['pull_l_n', 'pull_r_n', 'rel_pull', 'squeeze_l_n', 'squeeze_r_n', 'rel_squeeze'], 'desc': 'Hip Abduction/Adduction'},
    'Ön Bacak (Quadriseps)': {'keys': ['knee_ext_l_n', 'knee_ext_r_n', 'rel_knee'], 'desc': 'Knee Extension Max Kuvvet'}
}

# ── HESAPLAMALAR: Z-SCORE VE SIRALAMALAR (RANKING) ──
z_scores = pd.DataFrame(index=test_data.index)
ranks = pd.DataFrame(index=test_data.index)

for col, info in available_metrics_info.items():
    if col in test_data.columns and test_data[col].notna().any():
        c_mean = test_data[col].mean()
        c_std = test_data[col].std()
        
        if c_std > 0:
            z = (test_data[col] - c_mean) / c_std
            if info['invert']: z = -z
            z_scores[col] = z
            
        ranks[f"{col}_rank"] = test_data[col].rank(method='min', ascending=info['invert'])

if not z_scores.empty:
    test_data['composite_z'] = z_scores.mean(axis=1)
    test_data['Test_Skoru'] = np.clip((test_data['composite_z'] + 2.5) / 5 * 100, 0, 100)
else:
    test_data['Test_Skoru'] = 50

test_data['Genel_Sira'] = test_data['Test_Skoru'].rank(method='min', ascending=False).astype(int)

st.divider()

# ── GRAFİK MOTORLARI ──
def create_bullet_chart(title, player_val, team_min, team_avg, team_max, unit="", invert=False):
    if pd.isna(player_val): return None
    
    min_bound = min(0, team_min) if not invert else max(0, team_min - (team_max-team_min)*0.2)
    max_bound = max(team_max * 1.1, player_val * 1.1) if not invert else max(team_max, player_val) * 1.1
    
    fig = go.Figure()
    fig.add_shape(type="rect", x0=team_min, y0=0.2, x1=team_max, y1=0.8,
                  line=dict(width=0), fillcolor="rgba(156, 163, 175, 0.3)", layer="below")
    
    fig.add_trace(go.Bar(
        x=[player_val], y=[""], orientation='h',
        marker=dict(color=COLORS['RED']),
        width=0.35, hoverinfo='none', name="Oyuncu Değeri"
    ))
    
    fig.add_shape(type="line", x0=team_avg, y0=0.1, x1=team_avg, y1=0.9,
                  line=dict(color=COLORS['GRAY_900'], width=4), name="Takım Ortalaması")
                  
    fig.update_layout(
        title=dict(text=f"<b>{title}</b><br><span style='color:gray; font-size:11px'>Ort: {team_avg:.2f} | Aralık: [{team_min:.2f} - {team_max:.2f}]</span>", font=dict(size=14)),
        xaxis=dict(range=[min_bound, max_bound], title=unit, tickfont=dict(size=10), showgrid=True, gridcolor='#F3F4F6'),
        yaxis=dict(showticklabels=False),
        height=130, margin=dict(l=10, r=40, t=50, b=30),
        plot_bgcolor='white', paper_bgcolor='white',
        showlegend=False,
        annotations=[dict(x=player_val, y=0, text=f"<b>{player_val:.2f}</b>", showarrow=False, xanchor="left", xshift=8, font=dict(color=COLORS['RED'], size=15))]
    )
    return fig

def create_asym_gauge(title, val):
    if pd.isna(val): return None
    color = COLORS['DANGER'] if abs(val) >= 15 else ("#F59E0B" if abs(val) >= 10 else COLORS['SUCCESS'])
    direction = "L (Sol)" if val < 0 else "R (Sağ)"
    if val == 0: direction = "Simetrik"
    
    fig = go.Figure(go.Indicator(
        mode = "number+gauge", value = val, domain = {'x': [0.1, 0.9], 'y': [0.1, 0.9]},
        title = {'text': f"<b>{title}</b><br><span style='color: {color}; font-size:11px; font-weight:bold;'>Yön: {direction}</span>", 'font': {"size": 14}},
        number = {'valueformat': ".1f", 'suffix': "%", 'font': {'size': 22, 'color': color}},
        gauge = {
            'shape': "bullet", 'axis': {'range': [-30, 30], 'tickvals': [-30, -15, -10, 0, 10, 15, 30], 'ticktext': ['-30', '-15', '-10', '0', '10', '15', '30'], 'tickfont': {'size': 10}},
            'threshold': {'line': {'color': COLORS['GRAY_900'], 'width': 3}, 'thickness': 0.75, 'value': 0},
            'steps': [
                {'range': [-30, -15], 'color': "#fee2e2"}, {'range': [-15, -10], 'color': "#fef3c7"},
                {'range': [-10, 10], 'color': "#d1fae5"}, {'range': [10, 15], 'color': "#fef3c7"},
                {'range': [15, 30], 'color': "#fee2e2"}
            ],
            'bar': {'color': COLORS['GRAY_800'], 'thickness': 0.4}
        }
    ))
    fig.update_layout(height=130, margin=dict(t=40, b=30, l=120, r=30), paper_bgcolor="white")
    return fig

def create_spider_radar(player_z_scores, team_z_scores_mean=None, title="Kapasite Radarı"):
    categories = []
    values = []
    team_values = []
    hover_texts = []
    
    for cat_name, g_info in radar_categories_def.items():
        cols = [k for k in g_info['keys'] if k in player_z_scores and pd.notna(player_z_scores[k])]
        if cols:
            mean_z = player_z_scores[cols].mean()
            score = np.clip((mean_z + 2.5) / 5 * 100, 0, 100) 
            categories.append(cat_name)
            values.append(score)
            hover_texts.append(f"<b>{cat_name}</b><br>İçerik: {g_info['desc']}<br>Skor: %{score:.1f}")
            
            if team_z_scores_mean is not None:
                t_mean_z = team_z_scores_mean[cols].mean()
                t_score = np.clip((t_mean_z + 2.5) / 5 * 100, 0, 100)
                team_values.append(t_score)
            
    if len(categories) >= 3:
        fig = go.Figure()
        
        # Takım Ortalaması Alanı (Altta)
        if team_z_scores_mean is not None:
            fig.add_trace(go.Scatterpolar(
                r=team_values + [team_values[0]], theta=categories + [categories[0]],
                fill='toself', line_color=COLORS['GRAY_500'], fillcolor='rgba(156, 163, 175, 0.4)',
                name='Takım Ortalaması', hoverinfo='text',
                hovertext=[f"Takım Ort. Puan: %{v:.1f}" for v in team_values] + [f"Takım Ort. Puan: %{team_values[0]:.1f}"]
            ))
            
        # Oyuncu Profili (Üstte)
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]], theta=categories + [categories[0]],
            fill='toself', line_color=COLORS['RED'], fillcolor='rgba(227, 10, 23, 0.4)',
            name='Oyuncu', hoverinfo='text', hovertext=hover_texts + [hover_texts[0]]
        ))
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=14, color=COLORS['GRAY_800'])),
            polar=dict(radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=8))),
            showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            height=380, margin=dict(t=40, b=30, l=40, r=40)
        )
        return fig
    return None

# ── SEKMELER (TABS) ──────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "👤 ÇIKTI ALINABİLİR PROFİL", 
    "📊 DEĞİŞKEN ANALİZİ",
    "🏆 SIRALAMA MATRİSİ",
    "⭕ TEKİL NOKTA DAĞILIMI", 
    "📈 ÇAPRAZ SCATTER", 
    "⚔️ OYUNCU H2H (KARŞILAŞTIRMA)"
])

# ── TAB 1: ÇIKTI ALINABİLİR BİREYSEL PROFİL ──────────────────────────────────
with tab1:
    if search_player != "Seçilmedi":
        p_data = test_data[test_data['player_name'] == search_player].iloc[0]
        p_idx = test_data[test_data['player_name'] == search_player].index[0]
        p_z_scores = z_scores.loc[p_idx]
        team_z_mean = z_scores.mean()
        
        st.markdown(f"""
        <div style='background:white; border:1px solid #E5E7EB; border-left:8px solid {COLORS['RED']}; padding:20px; border-radius:12px; margin-bottom:15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <div>
                    <h2 style='margin:0; font-family:"Bebas Neue", sans-serif; color:{COLORS['GRAY_900']}; font-size:36px;'>{search_player.upper()}</h2>
                    <p style='margin:0; color:gray; font-size:14px;'>Yaş Grubu: <b>{age_group}</b> | Test Tarihi: <b>{p_data['tarih']}</b> | Boy: <b>{p_data.get('height_cm','-')} cm</b> | Kilo: <b>{p_data.get('bw_kg','-')} kg</b></p>
                </div>
                <div style='text-align:right;'>
                    <div style='font-size:12px; color:gray; font-weight:bold; text-transform:uppercase;'>Takım Sırası: {p_data.get('Genel_Sira', '-')} / {len(test_data)}</div>
                    <div style='font-size:38px; font-family:"Bebas Neue", sans-serif; color:{COLORS['RED']}; line-height:1;'>%{p_data.get('Test_Skoru',0):.1f}</div>
                    <div style='font-size:11px; color:gray;'>Genel Atletik Skor</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col_ai, col_radar = st.columns([2, 1])
        with col_ai:
            valid_z = p_z_scores.dropna()
            if not valid_z.empty:
                best_m = valid_z.idxmax()
                worst_m = valid_z.idxmin()
                best_score = np.clip((valid_z[best_m] + 2.5) / 5 * 100, 0, 100)
                
                max_asym_val, max_asym_name = 0, ""
                for c, v in asym_metrics.items():
                    if pd.notna(p_data.get(c)) and abs(p_data[c]) > max_asym_val:
                        max_asym_val = abs(p_data[c])
                        max_asym_name = v['name']

                ai_text = f"💡 **Akıllı Fiziksel Analiz Notu (Kapasite Özeti):**<br>"
                ai_text += f"<span style='font-size:12px; color:gray;'>*Not: Puanlar (0-100), oyuncunun test verilerinin takım ortalamasına olan Z-Skoru uzaklığı ile hesaplanır. Takım ortalaması tam olarak 50 Puandır.</span><br><br>"
                
                ai_text += f"• 🟢 **En Güçlü Yönü:** {available_metrics_info[best_m]['name']} (Skor: %{best_score:.0f}). Oyuncu bu metrikte takımın en elit seviyelerinde yer alıyor.<br>"
                
                eur_val = p_data.get('eur')
                if pd.notna(eur_val):
                    ai_text += f"• 🦵 **Kas Elastikiyeti (EUR):** CMJ ve SJ sıçramaları arasındaki esneme farkına bakılır. "
                    if eur_val <= 1.05: ai_text += f"Bu oyuncunun oranı {eur_val:.2f}. Çok düşük. Tendonlarını (Stretch-Shortening Cycle) iyi kullanamıyor. Plyometrik (zıplama) antrenmanlara ağırlık verilmeli.<br>"
                    elif eur_val >= 1.15: ai_text += f"Bu oyuncunun oranı {eur_val:.2f}. Yüksek bir oran. Patlayıcılığı iyi ancak temel maksimal kuvvetinde (SJ) eksiklik var.<br>"
                    else: ai_text += f"Bu oyuncunun oranı {eur_val:.2f}. Temel kuvvet ve esneklik (elastikiyet) dengesi kusursuz.<br>"

                if max_asym_val > 15:
                    ai_text += f"• ⚠️ **KRİTİK UYARI:** {max_asym_name} testinde sağ ve sol bacak arasında **%{max_asym_val:.1f}** asimetri tespit edildi! Kırmızı risk bölgesinde. Sakatlığı önlemek için acil kuvvet eşitleme protokolü uygulanmalı."
                elif max_asym_val > 10:
                    ai_text += f"• ⚠️ **Dikkat:** {max_asym_name} testinde %{max_asym_val:.1f} asimetri var, sarı bölgede. Takip edilmeli ve dengelenmeli."
                else:
                    ai_text += f"• ✅ **Mekanik Denge:** Oyuncunun tüm testlerdeki sağ-sol bacak kuvvet dengesi (Asimetri) sağlıklı ve simetrik sınırlarda (%10 altı)."
                
                st.markdown(f"<div style='background:#FFFBEB; border-left:4px solid #F59E0B; padding:15px; border-radius:8px; font-size:14px; color:#374151; line-height:1.6;'>{ai_text}</div>", unsafe_allow_html=True)
                
        with col_radar:
            radar_fig = create_spider_radar(p_z_scores, team_z_scores_mean=team_z_mean, title="Atletik Kapasite Ağı (Takım Kıyaslı)")
            if radar_fig: st.plotly_chart(radar_fig, width='stretch', config={'displayModeBar': False})

        st.markdown(f"""
        <div style='display:flex; gap:20px; align-items:center; background:#FAFAFA; padding:10px 20px; border-radius:8px; margin-top:20px; margin-bottom:10px; border:1px solid #E5E7EB;'>
            <span style='font-size:13px; font-weight:bold; color:#374151;'>GRAFİK OKUMA REHBERİ:</span>
            <div style='display:flex; align-items:center; gap:5px;'><div style='width:16px; height:16px; background:{COLORS['RED']}; border-radius:4px;'></div><span style='font-size:12px; color:gray;'>Oyuncu Değeri</span></div>
            <div style='display:flex; align-items:center; gap:5px;'><div style='width:4px; height:16px; background:{COLORS['GRAY_900']};'></div><span style='font-size:12px; color:gray;'>Takım Ortalaması</span></div>
            <div style='display:flex; align-items:center; gap:5px;'><div style='width:30px; height:16px; background:rgba(156, 163, 175, 0.3); border-radius:4px;'></div><span style='font-size:12px; color:gray;'>Takım Yayılımı (Min-Max)</span></div>
        </div>
        """, unsafe_allow_html=True)

        has_sprint = pd.notna(p_data.get('sprint_10m')) and pd.notna(p_data.get('sprint_20m')) and pd.notna(p_data.get('sprint_30m'))
        if has_sprint:
            distances = ['10m', '20m', '30m']
            p_times = [p_data['sprint_10m'], p_data['sprint_20m'], p_data['sprint_30m']]
            t_times = [test_data['sprint_10m'].mean(), test_data['sprint_20m'].mean(), test_data['sprint_30m'].mean()]
            
            fig_sprint = go.Figure()
            fig_sprint.add_trace(go.Scatter(x=distances, y=p_times, mode='lines+markers+text', name=search_player.upper(), line=dict(color=COLORS['RED'], width=3), text=[f"{t:.2f}" for t in p_times], textposition='bottom right'))
            fig_sprint.add_trace(go.Scatter(x=distances, y=t_times, mode='lines+markers', name='Takım Ort.', line=dict(color=COLORS['GRAY_800'], width=2, dash='dash')))
            fig_sprint.update_layout(title="<b>İvmelenme ve Hız Eğrisi (Split Times)</b>", height=250, margin=dict(t=40, b=20, l=20, r=20), yaxis=dict(autorange='reversed', title='Süre (sn)'), plot_bgcolor='white', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_sprint, width='stretch', config={'displayModeBar': False})

        def render_test_group(group_key, group_title, icon):
            cols_in_group = [k for k, v in available_metrics_info.items() if v['group'] == group_key and k in p_data and pd.notna(p_data[k])]
            asym_col = next((k for k, v in asym_metrics.items() if v['group'] == group_key and k in p_data and pd.notna(p_data[k])), None)
            
            if not cols_in_group and not asym_col: return
            
            st.markdown(f"<h4 style='color:{COLORS['GRAY_800']}; border-bottom:2px solid #E5E7EB; padding-bottom:5px; margin-top:25px;'>{icon} {group_title}</h4>", unsafe_allow_html=True)
            
            if asym_col:
                l_col = next((c for c in cols_in_group if '_l_' in c or ' Sol' in available_metrics_info[c]['name']), None)
                r_col = next((c for c in cols_in_group if '_r_' in c or ' Sağ' in available_metrics_info[c]['name']), None)
                
                b1, b2 = st.columns(2)
                with b1:
                    if l_col:
                        info = available_metrics_info[l_col]
                        fig = create_bullet_chart(info['name'], p_data[l_col], test_data[l_col].min(), test_data[l_col].mean(), test_data[l_col].max(), info['unit'], info['invert'])
                        if fig: st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
                with b2:
                    if r_col:
                        info = available_metrics_info[r_col]
                        fig = create_bullet_chart(info['name'], p_data[r_col], test_data[r_col].min(), test_data[r_col].mean(), test_data[r_col].max(), info['unit'], info['invert'])
                        if fig: st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
                
                ac1, ac2, ac3 = st.columns([1, 2, 1])
                with ac2:
                    fig_a = create_asym_gauge(asym_metrics[asym_col]['name'], p_data[asym_col])
                    if fig_a: st.plotly_chart(fig_a, width='stretch', config={'displayModeBar': False})
                    
            else:
                grid_cols = st.columns(3) if len(cols_in_group) >= 3 else st.columns(2)
                for idx, col in enumerate(cols_in_group):
                    with grid_cols[idx % len(grid_cols)]:
                        info = available_metrics_info[col]
                        fig = create_bullet_chart(info['name'], p_data[col], test_data[col].min(), test_data[col].mean(), test_data[col].max(), info['unit'], info['invert'])
                        if fig: st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

        render_test_group('jump', 'Genel Sıçrama Kapasitesi', '🦘')
        render_test_group('jump_asym', 'Tek Bacak Sıçrama (SLJ L/R)', '⚖️')
        render_test_group('speed', 'Hız ve İvmelenme', '⚡')
        render_test_group('nordic', 'Nordic (Hamstring) Kuvveti', '🦵')
        render_test_group('pull', 'Seated Hip Abduction (İç Bacak)', '🧲')
        render_test_group('squeeze', 'Seated Hip Adduction (Sıkıştırma)', '🗜️')
        render_test_group('knee', 'Knee Extension (Quadriseps)', '🦵')

    else:
        st.info("Detaylı profil raporunu (A4 PDF Çıktı formatı) görmek için yukarıdan bir oyuncu seçin.")

# ── TAB 2: DEĞİŞKEN ANALİZİ ──────────────────────────────────────────────────
with tab2:
    section_title("DEĞİŞKEN ANALİZİ (METRİK BAZLI TAKIM PROFİLİ)", "📊")
    
    avail_cols = [c for c in available_metrics_info.keys() if c in test_data.columns and test_data[c].notna().any()]
    
    if avail_cols:
        da1, da2 = st.columns([1, 2])
        with da1:
            sel_comp_metric = st.selectbox("İncelenecek Metrik", avail_cols, format_func=lambda x: available_metrics_info[x]['name'])
            info = available_metrics_info[sel_comp_metric]
            
            t_min = test_data[sel_comp_metric].min()
            t_max = test_data[sel_comp_metric].max()
            t_avg = test_data[sel_comp_metric].mean()
            t_std = test_data[sel_comp_metric].std()
            
            st.markdown(f"""
            <div style='background:white; border:1px solid #E5E7EB; border-radius:8px; padding:15px; margin-top:20px;'>
                <div style='font-size:12px; color:gray; text-transform:uppercase;'><b>{info['name']} Takım Özeti</b></div>
                <hr style='margin:10px 0;'>
                <div style='display:flex; justify-content:space-between; margin-bottom:5px;'><span style='color:gray'>Ortalama:</span> <b>{t_avg:.2f} {info['unit']}</b></div>
                <div style='display:flex; justify-content:space-between; margin-bottom:5px;'><span style='color:gray'>En İyi:</span> <b style='color:{COLORS['SUCCESS']}'>{t_min if info['invert'] else t_max:.2f} {info['unit']}</b></div>
                <div style='display:flex; justify-content:space-between; margin-bottom:5px;'><span style='color:gray'>En Kötü:</span> <b style='color:{COLORS['DANGER']}'>{t_max if info['invert'] else t_min:.2f} {info['unit']}</b></div>
                <div style='display:flex; justify-content:space-between;'><span style='color:gray'>Std. Sapma:</span> <b>±{t_std:.2f}</b></div>
            </div>
            """, unsafe_allow_html=True)
            
        with da2:
            df_sorted = test_data.dropna(subset=[sel_comp_metric]).sort_values(sel_comp_metric, ascending=not info['invert'])
            
            if info['invert']:
                df_sorted['color'] = np.where(df_sorted[sel_comp_metric] <= t_avg, COLORS['SUCCESS'], COLORS['DANGER'])
            else:
                df_sorted['color'] = np.where(df_sorted[sel_comp_metric] >= t_avg, COLORS['SUCCESS'], COLORS['DANGER'])
                
            fig_comp = px.bar(df_sorted, x=sel_comp_metric, y='player_name', orientation='h', text=sel_comp_metric,
                              color='color', color_discrete_map="identity",
                              labels={'player_name': 'Oyuncu', sel_comp_metric: f'{info["name"]} ({info["unit"]})'})
                         
            fig_comp.add_vline(x=t_avg, line_dash="dash", line_color=COLORS['GRAY_800'], annotation_text=f"Ort: {t_avg:.2f}")
            fig_comp.update_traces(texttemplate='%{text:.2f}' if 'sn' in info['unit'] else '%{text:.1f}', textposition='outside')
            fig_comp.update_layout(template='plotly_white', height=max(400, len(df_sorted)*30), showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_comp, width='stretch')

# ── TAB 3: SIRALAMA MATRİSİ (ISISI HARİTASI) ─────────────────────────────────
with tab3:
    section_title("TAKIM İÇİ SIRALAMA MATRİSİ (RANKING HEATMAP)", "🏆")
    st.info("Her oyuncunun ilgili testteki sırasını gösterir. Yeşil renkler takımın en iyilerini (1. 2. vs), kırmızı renkler ise en alt sıraları temsil eder.")
    
    matrix_cols = ['player_name', 'Genel_Sira']
    rename_matrix = {'player_name': 'OYUNCU', 'Genel_Sira': 'GENEL SIRA'}
    
    for col, info in available_metrics_info.items():
        rank_col = f"{col}_rank"
        if rank_col in ranks.columns and ranks[rank_col].notna().any():
            matrix_cols.append(rank_col)
            rename_matrix[rank_col] = info['name']
            test_data[rank_col] = ranks[rank_col]
            
    matrix_df = test_data.dropna(subset=['Genel_Sira'])[matrix_cols].sort_values('Genel_Sira').copy()
    matrix_df = matrix_df.rename(columns=rename_matrix)
    
    matrix_df = matrix_df.fillna(999) 
    rank_cols_only = [c for c in matrix_df.columns if c != 'OYUNCU']
    
    st.dataframe(
        matrix_df.style.format(precision=0).background_gradient(cmap='RdYlGn_r', subset=rank_cols_only, vmin=1, vmax=len(matrix_df)), 
        width='stretch', hide_index=True
    )

# ── TAB 4: TEKİL NOKTA DAĞILIMI (1D LADDER SCATTER) - YENİ EKLENDİ ───────────
with tab4:
    section_title("TEKİL DEĞİŞKEN NOKTA DAĞILIMI (1D SCATTER)", "⭕")
    st.markdown("Seçtiğiniz metriğe göre tüm oyuncuların sıralamasını ve birbirlerine olan gerçek mesafe farklarını 'halka halka' dağılım üzerinde isimleriyle inceleyin.")
    
    if avail_cols:
        sel_1d = st.selectbox("Dağılımı İncelenecek Metrik", avail_cols, format_func=lambda x: available_metrics_info[x]['name'], key="sel_1d")
        info = available_metrics_info[sel_1d]
        
        df_1d = test_data.dropna(subset=[sel_1d]).copy()
        
        # Rank hesaplama
        df_1d['Sira_Int'] = df_1d[sel_1d].rank(ascending=info['invert'], method='min').astype(int)
        df_1d['Label'] = df_1d['Sira_Int'].astype(str) + ". " + df_1d['player_name']
        
        # Renklendirme (Seçili oyuncu Kırmızı, diğerleri Gri/Siyah)
        df_1d['Renk'] = np.where(df_1d['player_name'] == search_player, COLORS['RED'], COLORS['GRAY_700'])
        
        fig_1d = px.scatter(df_1d, x=sel_1d, y='Sira_Int', text='Label',
                            labels={sel_1d: f"{info['name']} ({info['unit']})", 'Sira_Int': 'Sıralama (Liderden Sona)'})
        
        fig_1d.update_traces(marker=dict(size=14, color=df_1d['Renk'], line=dict(width=2, color='white')),
                             textposition='middle right', textfont=dict(size=11, color=df_1d['Renk'], weight='bold'))
        
        # Grafik eksen ve görünüm ayarları
        fig_1d.update_layout(
            yaxis=dict(autorange="reversed", showgrid=False, zeroline=False, showticklabels=False, title=""), # Y eksenini gizle, sadece sıralamayı ters yap
            xaxis=dict(showgrid=True, gridcolor="#F3F4F6", zeroline=False),
            height=max(400, len(df_1d)*35), plot_bgcolor='white', margin=dict(l=10, r=150)
        )
        
        # Eğer sprintse, x eksenini de ters çevir (Kısa süre solda (önde) dursun)
        if info['invert']: fig_1d.update_xaxes(autorange="reversed")
        
        st.plotly_chart(fig_1d, width='stretch', config={'displayModeBar': False})

# ── TAB 5: ÇAPRAZ DAĞILIM (SCATTER PLOT) ──────────────────────────────────────
with tab5:
    section_title("TEST METRİKLERİ ÇAPRAZ İLİŞKİ (SCATTER PLOT)", "📈")
    
    if len(avail_cols) >= 2:
        sc1, sc2, sc3 = st.columns([1, 1, 2])
        with sc1: x_axis = st.selectbox("X EKSENİ (Yatay)", avail_cols, format_func=lambda x: available_metrics_info[x]['name'], index=0)
        with sc2: y_axis = st.selectbox("Y EKSENİ (Dikey)", avail_cols, format_func=lambda x: available_metrics_info[x]['name'], index=1)
        with sc3: highlight_players = st.multiselect("Vurgulanacak Oyuncular (İsimleri Çıkar)", players_in_data, default=[search_player] if search_player != "Seçilmedi" else [])
            
        plot_df = test_data.dropna(subset=[x_axis, y_axis]).copy()
        
        plot_df['Kategori'] = np.where(plot_df['player_name'].isin(highlight_players), 'Seçili Oyuncular', 'Takım')
        plot_df['Text'] = np.where(plot_df['player_name'].isin(highlight_players), plot_df['player_name'], '')
        
        color_map = {'Seçili Oyuncular': COLORS['RED'], 'Takım': COLORS['GRAY_400']}
        
        fig_scatter = px.scatter(plot_df, x=x_axis, y=y_axis, color='Kategori', color_discrete_map=color_map,
                                 hover_name='player_name', text='Text',
                                 labels={x_axis: f"{available_metrics_info[x_axis]['name']} ({available_metrics_info[x_axis]['unit']})",
                                         y_axis: f"{available_metrics_info[y_axis]['name']} ({available_metrics_info[y_axis]['unit']})"})
        
        fig_scatter.update_traces(textposition='top center', textfont=dict(weight='bold', color=COLORS['GRAY_900']),
                                  marker=dict(size=12, line=dict(width=1, color='white')))
        
        fig_scatter.add_vline(x=plot_df[x_axis].mean(), line_dash="dash", line_color=COLORS['GRAY_500'], annotation_text="X Ort")
        fig_scatter.add_hline(y=plot_df[y_axis].mean(), line_dash="dash", line_color=COLORS['GRAY_500'], annotation_text="Y Ort")
        
        if available_metrics_info[x_axis]['invert']: fig_scatter.update_xaxes(autorange="reversed")
        if available_metrics_info[y_axis]['invert']: fig_scatter.update_yaxes(autorange="reversed")
        
        fig_scatter.update_layout(template='plotly_white', height=600, 
                                  title=f"<b>{available_metrics_info[x_axis]['name']} vs {available_metrics_info[y_axis]['name']}</b>",
                                  legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_scatter, width='stretch')

# ── TAB 6: OYUNCU H2H (KARŞILAŞTIRMA) ─────────────────────────────────────────
with tab6:
    section_title("OYUNCU KARŞILAŞTIRMASI (HEAD-TO-HEAD)", "⚔️")
    st.markdown("İki oyuncunun tüm fiziksel özelliklerini birbirleriyle ve takımla kıyaslayın (Değerler Z-Skoru üzerinden 0-100 standart puanına çevrilmiştir).")
    
    h2h_c1, h2h_c2 = st.columns(2)
    with h2h_c1: p1_sel = st.selectbox("1. Oyuncu", players_in_data, key="h2h_p1", index=0)
    with h2h_c2: p2_sel = st.selectbox("2. Oyuncu", players_in_data, key="h2h_p2", index=min(1, len(players_in_data)-1))
    
    if p1_sel and p2_sel and p1_sel != p2_sel:
        p1_d = test_data[test_data['player_name'] == p1_sel].iloc[0]
        p2_d = test_data[test_data['player_name'] == p2_sel].iloc[0]
        p1_z = z_scores.loc[p1_d.name]
        p2_z = z_scores.loc[p2_d.name]
        
        # İki Oyuncu İçin Karşılaştırmalı H2H Radarı
        radar_cols = st.columns([1, 2, 1])
        with radar_cols[1]:
            categories = []
            v1 = []; v2 = []
            
            for cat_name, g_info in radar_categories_def.items():
                cols = [k for k in g_info['keys'] if k in p1_z and pd.notna(p1_z[k]) and pd.notna(p2_z[k])]
                if cols:
                    categories.append(cat_name)
                    v1.append(np.clip((p1_z[cols].mean() + 2.5) / 5 * 100, 0, 100))
                    v2.append(np.clip((p2_z[cols].mean() + 2.5) / 5 * 100, 0, 100))
                    
            if len(categories) >= 3:
                fig_h2h_radar = go.Figure()
                fig_h2h_radar.add_trace(go.Scatterpolar(r=v1 + [v1[0]], theta=categories + [categories[0]], fill='toself', name=p1_sel, line_color=COLORS['RED']))
                fig_h2h_radar.add_trace(go.Scatterpolar(r=v2 + [v2[0]], theta=categories + [categories[0]], fill='toself', name=p2_sel, line_color=COLORS['BLACK']))
                fig_h2h_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=8))), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5), height=380, margin=dict(t=20, b=20), title=dict(text="Kapasite Eşleşme Radarı", x=0.5))
                st.plotly_chart(fig_h2h_radar, width='stretch', config={'displayModeBar': False})
        
        st.divider()

        comp_metrics = []
        p1_z_list = []; p2_z_list = []
        for col, info in available_metrics_info.items():
            if col in z_scores.columns and pd.notna(p1_d.get(col)) and pd.notna(p2_d.get(col)):
                comp_metrics.append(info['name'])
                p1_z_list.append(np.clip((z_scores.loc[p1_d.name, col] + 2.5) / 5 * 100, 0, 100))
                p2_z_list.append(np.clip((z_scores.loc[p2_d.name, col] + 2.5) / 5 * 100, 0, 100))
                
        if comp_metrics:
            fig_h2h = go.Figure()
            fig_h2h.add_trace(go.Bar(name=p1_sel, x=comp_metrics, y=p1_z_list, marker_color=COLORS['RED']))
            fig_h2h.add_trace(go.Bar(name=p2_sel, x=comp_metrics, y=p2_z_list, marker_color=COLORS['BLACK']))
            
            fig_h2h.add_hline(y=50, line_dash="dash", line_color=COLORS['GRAY_500'], annotation_text="Takım Ortalaması")
            
            fig_h2h.update_layout(
                barmode='group', template='plotly_white', height=450,
                title="<b>Tüm Testlerde Bar Karşılaştırması (Z-Score 0-100)</b>",
                yaxis=dict(title="Skor (0-100)", range=[0, 110]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_h2h, width='stretch')

st.markdown('<div class="tff-footer"><p>Performans Analiz Sistemi · Fiziksel Performans Laboratuvarı</p></div>', unsafe_allow_html=True)