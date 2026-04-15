import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import re
import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler

from config import (METRICS, METRICS_BASE, METRICS_ACC_DEC,
                    METRICS_N, RADAR_METRICS, PRIMARY_METRICS, DEFAULT_MINUTES)
from styles import COLORS, PLAYER_PALETTE


# ─────────────────────────────────────────────────────────────────────────────
# RENK YARDIMCILARI
# ─────────────────────────────────────────────────────────────────────────────

def hex_to_rgba(hex_color: str, alpha: float = 0.15) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"


def day_color(tip, alpha=1.0):
    if 'MATCH' in str(tip).upper():
        return f"rgba(13,13,13,{alpha})"
    return f"rgba(227,10,23,{alpha})"


def percentile_color(pct: float) -> str:
    """0-100 percentile → red to green gradient."""
    r = int(227 * (1 - pct/100) + 5  * (pct/100))
    g = int(10  * (1 - pct/100) + 150 * (pct/100))
    b = int(23  * (1 - pct/100) + 96  * (pct/100))
    return f"rgb({r},{g},{b})"


# ─────────────────────────────────────────────────────────────────────────────
# PERCENTİLE RANK (SKORLAMA) HESAPLAMASI
# ─────────────────────────────────────────────────────────────────────────────

def calculate_percentile_rank(player_values: pd.Series, population_values: pd.Series) -> float:
    if population_values.dropna().empty or player_values.dropna().empty:
        return 50.0
    player_mean = float(player_values.dropna().mean())
    pop = population_values.dropna().values
    n = len(pop)
    n_less = np.sum(pop < player_mean)
    n_equal = np.sum(pop == player_mean)
    pct = (n_less + 0.5 * n_equal) / n * 100
    return round(float(pct), 1)


def calculate_composite_score(player_data: pd.DataFrame,
                               population_data: pd.DataFrame,
                               session_filter: str = "ALL") -> dict:
    def _filter(df):
        if session_filter == "TRAINING":
            return df[df['tip'].str.upper() == 'TRAINING']
        if session_filter == "MATCH":
            return df[df['tip'].str.upper() == 'MATCH']
        return df

    p = _filter(player_data)
    pop = _filter(population_data)

    result = {}
    valid_metrics = []
    
    for m in PRIMARY_METRICS:
        if m not in p.columns or p[m].dropna().empty:
            continue
        if m not in pop.columns or pop[m].dropna().empty:
            continue
        pct = calculate_percentile_rank(p[m], pop[m])
        result[m] = pct
        valid_metrics.append(pct)

    result['composite'] = round(np.mean(valid_metrics), 1) if valid_metrics else 0.0
    return result


def calculate_player_stats(player_data: pd.DataFrame) -> dict:
    if player_data.empty:
        return {}
    
    train = player_data[player_data['tip'].str.contains('TRAINING', na=False, case=False)]
    match = player_data[player_data['tip'].str.contains('MATCH',    na=False, case=False)]
    
    total_min = player_data['minutes'].sum()
    return {
        'camp_count':            player_data['camp_id'].nunique(),
        'session_count':         player_data['tarih'].nunique(), 
        'match_count':           match['tarih'].nunique() if not match.empty else 0, 
        'training_count':        train['tarih'].nunique() if not train.empty else 0,
        'avg_distance_training': train['total_distance'].mean() if not train.empty else 0,
        'avg_distance_match':    match['total_distance'].mean()  if not match.empty else 0,
        'avg_training_minutes':  train['minutes'].mean()         if not train.empty else 0,
        'avg_match_minutes':     match['minutes'].mean()         if not match.empty else 0,
        'distance_per_90':       (player_data['total_distance'].sum() / total_min * 90) if total_min > 0 else 0,
        'max_speed':             player_data['smax_kmh'].max()   if 'smax_kmh' in player_data else 0,
        'avg_player_load':       player_data['player_load'].mean() if 'player_load' in player_data else 0,
    }

get_player_stats = calculate_player_stats


# ─────────────────────────────────────────────────────────────────────────────
# MİN / MAX / ORT ÖZET TABLOSU VE SIRALAMA
# ─────────────────────────────────────────────────────────────────────────────

def calculate_rank_and_percentile(df, metric, player_val, ascending=False):
    if df.empty or metric not in df.columns or pd.isna(player_val) or player_val == 0:
        return {"rank_str": "—", "percentile": 0, "rank_int": 0, "total": 0}
        
    valid_data = df[df[metric] > 0][metric].copy()
    total_players = len(valid_data)
    
    if total_players == 0:
         return {"rank_str": "—", "percentile": 0, "rank_int": 0, "total": 0}

    valid_data_sorted = valid_data.sort_values(ascending=ascending).reset_index(drop=True)
    rank_int = int(valid_data.rank(ascending=ascending, method='min').loc[df[metric] == player_val].iloc[0])
    
    if not ascending:
        percentile = (valid_data < player_val).sum() / total_players * 100
    else:
        percentile = (valid_data > player_val).sum() / total_players * 100
        
    percentile = min(max(percentile, 1), 99) 

    return {
        "rank_str": f"{rank_int}/{total_players}",
        "percentile": round(percentile, 1),
        "rank_int": rank_int,
        "total": total_players
    }

def format_metric_value(val, metric):
    if pd.isna(val): return "—"
    fmt = METRICS.get(metric, {}).get('format', '{:.1f}')
    try:
        return fmt.format(val)
    except:
        return str(val)

def build_stats_table(player_data: pd.DataFrame, team_data: pd.DataFrame) -> pd.DataFrame:
    all_m = [m for m in PRIMARY_METRICS if m in player_data.columns and player_data[m].dropna().any()]

    rows = []
    for m in all_m:
        p_valid_min = player_data[m].replace(0, np.nan).dropna()
        t_valid_min = team_data[m].replace(0, np.nan).dropna() if not team_data.empty else pd.Series(dtype=float)

        p   = player_data[m].dropna()
        t   = team_data[m].dropna()  if not team_data.empty else pd.Series(dtype=float)
        mi  = METRICS.get(m, {})

        pct = calculate_percentile_rank(p, t) if not t.empty else None

        rows.append({
            'METRİK':         mi.get('display', m).upper(),
            'BİRİM':          mi.get('unit', ''),
            'OYUNCU MİN':     f"{p_valid_min.min():.1f}"  if not p_valid_min.empty else '—',
            'OYUNCU ORT.':    f"{p.mean():.1f}" if not p.empty else '—',
            'OYUNCU MAX':     f"{p.max():.1f}"  if not p.empty else '—',
            'TAKIM MİN':      f"{t_valid_min.min():.1f}"  if not t_valid_min.empty else '—',
            'TAKIM ORT.':     f"{t.mean():.1f}" if not t.empty else '—',
            'TAKIM MAX':      f"{t.max():.1f}"  if not t.empty else '—',
            'SKOR':           f"%{pct:.0f}"      if pct is not None else '—',
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# IMPACT SCORE & OBJEKTİF KARAR MOTORU 
# ─────────────────────────────────────────────────────────────────────────────

def calculate_impact_score_engine(df):
    if df.empty: return df
    
    d = df.copy()
    d = d[d['minutes'] > 0].copy()
    
    pm_metrics = ['total_distance', 'metrage', 'dist_20_25', 'dist_25_plus', 
                  'dist_acc_3', 'dist_dec_3', 'player_load', 'amp']
                  
    for m in pm_metrics:
        if m in d.columns:
            d[f'{m}_pm'] = d[m] / d['minutes']
            
    d['explosive_pm'] = 0
    if 'dist_acc_3_pm' in d.columns and 'dist_dec_3_pm' in d.columns:
        d['explosive_pm'] = (d['dist_acc_3_pm'] + d['dist_dec_3_pm'].abs()) / 2
        
    d['metabolic_pm'] = 0
    if 'amp_pm' in d.columns and 'metrage_pm' in d.columns:
        d['metabolic_pm'] = (d['amp_pm'] + d['metrage_pm']) / 2
    elif 'amp_pm' in d.columns:
        d['metabolic_pm'] = d['amp_pm']

    def apply_z(group):
        cols_to_z = [f'{m}_pm' for m in pm_metrics] + ['explosive_pm', 'metabolic_pm', 'smax_kmh']
        for col in cols_to_z:
            if col in group.columns and group[col].std() > 0:
                group[f'{col}_z'] = (group[col] - group[col].mean()) / group[col].std()
            else:
                group[f'{col}_z'] = 0
        return group

    d = d.groupby(['tarih', 'tip'], group_keys=False).apply(apply_z)
    
    w = {
        'dist_25_plus_pm_z': 0.25,
        'explosive_pm_z':    0.20,
        'player_load_pm_z':  0.20,
        'total_distance_pm_z': 0.15,
        'smax_kmh_z':        0.10,
        'metabolic_pm_z':    0.10
    }
    
    d['impact_raw'] = 0
    for col, weight in w.items():
        if col in d.columns:
            d['impact_raw'] += d[col] * weight
            
    d['impact_score'] = ((d['impact_raw'] + 2.5) / 5 * 100).clip(0, 100).round(1)
    
    def get_objective_status(score):
        if score >= 80: return "Elit (+1.5 SD)"
        if score >= 60: return "Ort. Üstü (+0.5 SD)"
        if score >= 40: return "Ortalama Standardı"
        if score >= 20: return "Ort. Altı (-0.5 SD)"
        return "Düşük (-1.5 SD)"

    d['status_tag'] = d['impact_score'].apply(get_objective_status)
    return d

def calculate_development_stats(current_df, history_df):
    metrics = ['impact_score', 'dist_25_plus_pm', 'explosive_pm', 'player_load_pm', 'total_distance_pm']
    avail_metrics = [m for m in metrics if m in current_df.columns and m in history_df.columns]
    curr_avg = current_df.groupby('player_name')[avail_metrics].mean()
    hist_avg = history_df.groupby('player_name')[avail_metrics].mean()
    dev_df = ((curr_avg - hist_avg) / hist_avg * 100).round(1)
    return dev_df

def style_development_table(df):
    def color_val(val):
        if pd.isna(val): return ''
        if val >= 10:  return 'background-color: #065f46; color: white'
        if val >= 5:   return 'background-color: #10b981; color: white'
        if val <= -10: return 'background-color: #991b1b; color: white'
        if val <= -5:  return 'background-color: #f97316; color: white'
        return 'background-color: #fef08a; color: black'
    return df.style.map(color_val)


# ─────────────────────────────────────────────────────────────────────────────
# BENZER OYUNCU BULMA (COSINE SIMILARITY ENGINE)
# ─────────────────────────────────────────────────────────────────────────────

def find_similar_players(player_name, df, metrics):
    """
    Kosinüs Benzerliği kullanarak seçilen oyuncuya en yakın profil eşleşmelerini yapar.
    """
    if df.empty or player_name not in df['player_name'].values:
        return None

    # 1. Oyuncu bazlı metrik ortalamalarını al
    player_averages = df.groupby('player_name')[metrics].mean().fillna(0)
    
    # 2. Normalizasyon: Birimleri eşitlemek için Min-Max Scaling (0-1 arası)
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(player_averages)
    scaled_df = pd.DataFrame(scaled_data, index=player_averages.index, columns=metrics)
    
    # 3. Referans oyuncunun vektörü
    target_vector = scaled_df.loc[[player_name]]
    
    # 4. Kosinüs Benzerliği Hesapla
    similarities = cosine_similarity(target_vector, scaled_df)[0]
    
    # 5. Sonuçları DataFrame'e dönüştür
    similarity_df = pd.DataFrame({
        'OYUNCU': scaled_df.index,
        'BENZERLİK (%)': (similarities * 100).round(1)
    })
    
    # Kendisini listeden çıkar ve büyükten küçüğe sırala
    similarity_df = similarity_df[similarity_df['OYUNCU'] != player_name]
    return similarity_df.sort_values('BENZERLİK (%)', ascending=False).reset_index(drop=True)


def plot_dual_radar(p1_name, p1_data, p2_name, p2_data, metrics_list):
    """İki oyuncuyu karşılaştırmalı radar grafiğinde çizer."""
    labels = [METRICS.get(m, {}).get('display', m).upper() for m in metrics_list]
    
    # Maksimum değerlere göre normalizasyon (0-100 görselleştirme için)
    p1_vals, p2_vals = [], []
    for m in metrics_list:
        p1_m = p1_data[m].mean()
        p2_m = p2_data[m].mean()
        max_m = max(p1_m, p2_m, 1)
        p1_vals.append((p1_m / max_m) * 100)
        p2_vals.append((p2_m / max_m) * 100)

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=p1_vals, theta=labels, fill='toself', name=p1_name, line_color=COLORS['RED']))
    fig.add_trace(go.Scatterpolar(r=p2_vals, theta=labels, fill='toself', name=p2_name, line_color=COLORS['BLACK']))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 110])),
        showlegend=True, height=480, margin=dict(l=60, r=60, t=40, b=40)
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT HELPER
# ─────────────────────────────────────────────────────────────────────────────

_FONT = 'DM Sans, system-ui, sans-serif'
_FONT_TITLE = 'Bebas Neue, sans-serif'

def _base_layout(title='', height=480, **kw):
    d = dict(
        title=dict(text=f"<b>{title}</b>" if title else '',
                   font=dict(family=_FONT_TITLE, size=24, color=COLORS['GRAY_900'])),
        template='plotly_white',
        height=height,
        font=dict(family=_FONT, size=12, color=COLORS['GRAY_700']),
        plot_bgcolor='#FAFAFA',
        paper_bgcolor=COLORS['WHITE'],
        margin=dict(l=60, r=40, t=60, b=60),
    )
    d.update(kw)
    return d


# ─────────────────────────────────────────────────────────────────────────────
# PERFORMANS GRAFİKLERİ
# ─────────────────────────────────────────────────────────────────────────────

def plot_player_performance_with_band(df_player, df_team, metric, age_group=''):
    if df_player.empty or metric not in df_player.columns:
        return go.Figure()

    dp = df_player.sort_values('tarih').copy()
    dp['tarih_str'] = dp['tarih'].dt.strftime('%d.%m')

    dt = (df_team.groupby('tarih')[metric]
          .agg(mean='mean', mn='min', mx='max')
          .reset_index().sort_values('tarih'))
    dt['tarih_str'] = dt['tarih'].dt.strftime('%d.%m')

    m_info  = METRICS.get(metric, {'display': metric, 'unit': ''})
    title   = f"{m_info['display']} ({m_info['unit']})" if m_info['unit'] else m_info['display']
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dt['tarih_str'], y=dt['mx'],
        mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip',
    ))
    fig.add_trace(go.Scatter(
        x=dt['tarih_str'], y=dt['mn'],
        mode='lines', line=dict(width=0),
        fill='tonexty', fillcolor=COLORS['BAND_FILL'],
        name='Takım Aralığı', hoverinfo='skip',
    ))
    fig.add_trace(go.Scatter(
        x=dt['tarih_str'], y=dt['mean'],
        mode='lines+markers', name='Takım Ort.',
        line=dict(color=COLORS['GRAY_500'], width=2, dash='dot'),
        marker=dict(size=6, color=COLORS['GRAY_500']),
    ))
    vals = dp[metric].fillna(0)
    bar_c = [day_color(t, 0.88) for t in dp['tip']]

    fig.add_trace(go.Bar(
        x=dp['tarih_str'], y=vals, name='Oyuncu',
        marker=dict(color=bar_c, line=dict(color='rgba(0,0,0,0.06)', width=1)),
        text=[f"{v:.1f}" for v in vals],
        textposition='outside',
        textfont=dict(size=11, family=_FONT, color=COLORS['GRAY_900']),
    ))

    layout = _base_layout(title.upper())
    layout.update(
        barmode='overlay',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                    font=dict(size=11, weight='bold')),
        xaxis=dict(title='Tarih', tickangle=-30, gridcolor='#F3F4F6',
                   tickfont=dict(family=_FONT, size=11, weight='bold')),
        yaxis=dict(title=m_info['unit'], gridcolor='#F3F4F6',
                   tickfont=dict(family=_FONT, size=11)),
    )
    fig.update_layout(**layout)
    return fig


def plot_min_max_avg(df_player, df_team, metric):
    if df_player.empty or metric not in df_player.columns:
        return go.Figure()

    p_val = df_player[metric].dropna().mean()
    t_valid = df_team[metric].replace(0, np.nan).dropna()
    
    t_min = t_valid.min()  if not t_valid.empty else 0
    t_avg = df_team[metric].dropna().mean()  if not df_team.empty else 0
    t_max = df_team[metric].dropna().max()   if not df_team.empty else 1

    m_info = METRICS.get(metric, {'display': metric, 'unit': ''})

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[t_max], y=[''], orientation='h',
        marker=dict(color=COLORS['BAND_FILL'], line_width=0),
        name='Takım Max', showlegend=False,
    ))
    fig.add_trace(go.Bar(
        x=[t_avg], y=[''], orientation='h',
        marker=dict(color='rgba(107,114,128,0.3)', line_width=0),
        name='Takım Ort.', showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=[p_val], y=[''],
        mode='markers',
        marker=dict(color=COLORS['RED'], size=22, symbol='diamond',
                    line=dict(color='white', width=2)),
        name='Oyuncu',
    ))
    fig.update_layout(
        barmode='overlay',
        height=110, margin=dict(l=10, r=10, t=35, b=10),
        title=dict(text=m_info['display'].upper(), font=dict(family=_FONT_TITLE, size=16)),
        xaxis=dict(title=m_info['unit'], gridcolor='#F3F4F6', tickfont=dict(weight='bold')),
        yaxis=dict(visible=False),
        plot_bgcolor='#FAFAFA', paper_bgcolor=COLORS['WHITE'],
        showlegend=False,
        font=dict(family=_FONT, size=11),
    )
    return fig


def plot_percentile_gauge(pct: float, label: str) -> go.Figure:
    color = percentile_color(pct)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        title=dict(text=label.upper(), font=dict(family=_FONT, size=13, color=COLORS['GRAY_800'], weight='bold')),
        number=dict(suffix="%", font=dict(family=_FONT_TITLE, size=28, color=color)),
        gauge=dict(
            axis=dict(range=[0, 100], tickfont=dict(size=10, weight='bold')),
            bar=dict(color=color),
            bgcolor=COLORS['GRAY_100'],
            borderwidth=0,
            steps=[
                dict(range=[0,  25], color='rgba(220,38,38,0.12)'),
                dict(range=[25, 50], color='rgba(217,119,6,0.10)'),
                dict(range=[50, 75], color='rgba(37,99,235,0.10)'),
                dict(range=[75,100], color='rgba(5,150,105,0.10)'),
            ],
            threshold=dict(line=dict(color=COLORS['GRAY_500'], width=3), thickness=0.85, value=50),
        ),
    ))
    fig.update_layout(height=180, margin=dict(l=15, r=15, t=35, b=15), paper_bgcolor=COLORS['WHITE'])
    return fig


def plot_player_radar(player_data, team_data, radar_metrics=None):
    if radar_metrics is None: radar_metrics = RADAR_METRICS
    metrics = [m for m in radar_metrics if m in player_data.columns and player_data[m].notna().any()]
    if not metrics: return go.Figure()

    p_vals, t_avgs, labels = [], [], []
    for m in metrics:
        mx = team_data[m].max() if not team_data.empty and team_data[m].max() > 0 else 1
        p_vals.append(min((player_data[m].mean() / mx) * 100, 110))
        t_avgs.append(min((team_data[m].mean()  / mx) * 100, 110))
        labels.append(METRICS.get(m, {}).get('display', m).upper())

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=p_vals, theta=labels, fill='toself', name='Oyuncu',
        line=dict(color=COLORS['RED'], width=3), fillcolor=hex_to_rgba(COLORS['RED'], 0.2),
    ))
    fig.add_trace(go.Scatterpolar(
        r=t_avgs, theta=labels, fill='none', name='Takım Ort.',
        line=dict(color=COLORS['GRAY_500'], width=2, dash='dash'),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor='#FAFAFA',
            radialaxis=dict(visible=True, range=[0, 110], gridcolor='#E5E7EB', tickfont=dict(size=10)),
            angularaxis=dict(tickfont=dict(size=11, family=_FONT, color=COLORS['GRAY_800'], weight='bold'), gridcolor='#E5E7EB'),
        ),
        showlegend=True, height=500, paper_bgcolor=COLORS['WHITE'],
        legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5)
    )
    return fig


def plot_radar_comparison_multiple(players_dict: dict, team_data: pd.DataFrame, radar_metrics=None) -> go.Figure:
    if radar_metrics is None: radar_metrics = RADAR_METRICS
    metrics = [m for m in radar_metrics if m in team_data.columns and team_data[m].notna().any()]
    if not metrics: return go.Figure()

    labels = [METRICS.get(m, {}).get('display', m).upper() for m in metrics]
    fig = go.Figure()

    for i, (name, data) in enumerate(players_dict.items()):
        vals = []
        for m in metrics:
            mx = team_data[m].max()
            vals.append(min((data[m].mean() / mx) * 100, 110) if mx > 0 else 0)

        clr = PLAYER_PALETTE[i % len(PLAYER_PALETTE)]
        fig.add_trace(go.Scatterpolar(
            r=vals, theta=labels, fill='toself', name=name.upper(),
            line=dict(color=clr, width=2.5), fillcolor=hex_to_rgba(clr, 0.15),
        ))

    fig.update_layout(
        polar=dict(
            bgcolor='#FAFAFA',
            radialaxis=dict(visible=True, range=[0, 110], gridcolor='#E5E7EB', tickfont=dict(size=10)),
            angularaxis=dict(tickfont=dict(size=11, family=_FONT, color=COLORS['GRAY_800'], weight='bold'), gridcolor='#E5E7EB'),
        ),
        showlegend=True, height=540, paper_bgcolor=COLORS['WHITE'],
        legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5)
    )
    return fig


def plot_day_comparison(camp_data: pd.DataFrame, day1, day2, metric: str) -> go.Figure:
    d1 = camp_data[camp_data['tarih'].dt.normalize() == pd.Timestamp(day1).normalize()].copy()
    d2 = camp_data[camp_data['tarih'].dt.normalize() == pd.Timestamp(day2).normalize()].copy()

    if d1.empty or d2.empty: return go.Figure()

    players = sorted(set(d1['player_name']) | set(d2['player_name']))
    d1_dict = dict(zip(d1['player_name'], d1[metric]))
    d2_dict = dict(zip(d2['player_name'], d2[metric]))

    v1 = [d1_dict.get(p, None) for p in players]
    v2 = [d2_dict.get(p, None) for p in players]

    label1 = pd.Timestamp(day1).strftime('%d.%m.%Y')
    label2 = pd.Timestamp(day2).strftime('%d.%m.%Y')
    m_info = METRICS.get(metric, {'display': metric, 'unit': ''})

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name=label1, x=players, y=v1, marker=dict(color=COLORS['RED'], opacity=0.9),
        text=[f"{v:.1f}" if v else '' for v in v1], textposition='outside',
        textfont=dict(family=_FONT, size=10, weight='bold'),
    ))
    fig.add_trace(go.Bar(
        name=label2, x=players, y=v2, marker=dict(color=COLORS['BLACK'], opacity=0.9),
        text=[f"{v:.1f}" if v else '' for v in v2], textposition='outside',
        textfont=dict(family=_FONT, size=10, weight='bold'),
    ))
    layout = _base_layout(f"{m_info['display'].upper()} — GÜN KARŞILAŞTIRMASI", height=480)
    layout.update(barmode='group', xaxis=dict(tickangle=-35), yaxis=dict(title=m_info['unit']))
    fig.update_layout(**layout)
    return fig


def plot_camp_comparison(camp1_data: pd.DataFrame, camp2_data: pd.DataFrame, metric: str, camp1_label: str = 'KAMP 1', camp2_label: str = 'KAMP 2') -> go.Figure:
    players = sorted(set(camp1_data['player_name']) | set(camp2_data['player_name']))
    v1_dict = camp1_data.groupby('player_name')[metric].mean().to_dict()
    v2_dict = camp2_data.groupby('player_name')[metric].mean().to_dict()

    v1 = [v1_dict.get(p, None) for p in players]
    v2 = [v2_dict.get(p, None) for p in players]

    m_info = METRICS.get(metric, {'display': metric, 'unit': ''})
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name=camp1_label.upper(), x=players, y=v1, marker=dict(color=COLORS['RED'], opacity=0.9),
        text=[f"{v:.1f}" if v else '' for v in v1], textposition='outside',
        textfont=dict(family=_FONT, size=10, weight='bold'),
    ))
    fig.add_trace(go.Bar(
        name=camp2_label.upper(), x=players, y=v2, marker=dict(color=COLORS['BLACK'], opacity=0.9),
        text=[f"{v:.1f}" if v else '' for v in v2], textposition='outside',
        textfont=dict(family=_FONT, size=10, weight='bold'),
    ))
    layout = _base_layout(f"{m_info['display'].upper()} — KAMP KARŞILAŞTIRMASI", height=480)
    layout.update(barmode='group', xaxis=dict(tickangle=-35), yaxis=dict(title=m_info['unit']))
    fig.update_layout(**layout)
    return fig


def plot_daily_ranking(camp_data, tarih, metric, ascending=False):
    day = camp_data[camp_data['tarih'] == tarih].copy()
    if day.empty: return None
        
    day['_rank'] = day[metric].rank(ascending=False, method='min').astype(int)
    day = day.sort_values(metric, ascending=ascending).reset_index(drop=True)
    n = len(day)
    
    bar_c = [day_color(t, max(0.4, 1 - (i/max(n-1,1))*0.55)) for i, t in enumerate(day['tip'])]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=day['player_name'], x=day[metric], orientation='h',
        marker=dict(color=bar_c, line=dict(color='rgba(0,0,0,0.06)', width=1)),
        text=[f"  #{r}   {v:.1f}" for r, v in zip(day['_rank'], day[metric])],
        textposition='inside', insidetextanchor='start',
        textfont=dict(color='white', size=11, family=_FONT, weight='bold'),
        hovertemplate='<b>%{y}</b><br>%{x:.2f}<extra></extra>',
    ))
    
    m_info = METRICS.get(metric, {'display': metric, 'unit': ''})
    layout = _base_layout(m_info['display'].upper(), height=max(400, n * 30))
    layout.update(xaxis=dict(title=m_info['unit']), yaxis=dict(autorange="reversed"), showlegend=False)
    fig.update_layout(**layout)
    return fig


def plot_scatter(data: pd.DataFrame, x_metric: str, y_metric: str, color_by: str = 'player_name', highlight_player: str = None, show_avg_lines: bool = True) -> go.Figure:
    df = data.dropna(subset=[x_metric, y_metric]).copy()
    if df.empty: return go.Figure()

    x_info = METRICS.get(x_metric, {'display': x_metric, 'unit': ''})
    y_info = METRICS.get(y_metric, {'display': y_metric, 'unit': ''})

    fig = go.Figure()
    groups = df.groupby(df['tip'].str.upper().str.strip()) if color_by == 'tip' else df.groupby('player_name')
    palette = {'TRAINING': COLORS['RED'], 'MATCH': COLORS['BLACK']} if color_by == 'tip' else {p: PLAYER_PALETTE[i % len(PLAYER_PALETTE)] for i, p in enumerate(df['player_name'].unique())}

    for group_name, group_df in groups:
        is_hl   = (highlight_player and group_name == highlight_player)
        clr     = palette.get(str(group_name).upper() if color_by=='tip' else group_name, COLORS['GRAY_400'])
        size    = 16 if is_hl else 10
        opacity = 1.0 if is_hl else 0.7
        mode    = 'markers+text' if is_hl else 'markers'

        hover  = '<b>%{customdata[0]}</b><br>' + f'{x_info["display"].upper()}: %{{x:.1f}} {x_info["unit"]}<br>' + f'{y_info["display"].upper()}: %{{y:.1f}} {y_info["unit"]}<br>' + '%{customdata[1]}<extra></extra>'
        customdata = group_df[['player_name','tip']].values if 'player_name' in group_df else None

        fig.add_trace(go.Scatter(
            x=group_df[x_metric], y=group_df[y_metric], mode=mode, name=str(group_name).upper(),
            marker=dict(color=clr, size=size, opacity=opacity, line=dict(color='white', width=2 if is_hl else 0.5), symbol='diamond' if is_hl else 'circle'),
            text=group_df['player_name'].str.upper() if is_hl else None, textposition='top center',
            textfont=dict(size=11, family=_FONT, color=clr, weight='bold'), hovertemplate=hover, customdata=customdata,
        ))

    if show_avg_lines:
        x_avg = df[x_metric].mean(); y_avg = df[y_metric].mean()
        fig.add_vline(x=x_avg, line_dash='dash', line_color=COLORS['GRAY_500'], line_width=1.5, annotation_text=f"ORT: {x_avg:.1f}")
        fig.add_hline(y=y_avg, line_dash='dash', line_color=COLORS['GRAY_500'], line_width=1.5, annotation_text=f"ORT: {y_avg:.1f}")

    layout = _base_layout(f"{x_info['display'].upper()} vs {y_info['display'].upper()}", height=600)
    layout.update(xaxis=dict(title=x_info['display'].upper()), yaxis=dict(title=y_info['display'].upper()))
    fig.update_layout(**layout)
    return fig


def plot_player_comparison(p1_data, p2_data, metric, team_data=None, p1_name='OYUNCU 1', p2_name='OYUNCU 2'):
    names, values, colors = [p1_name.upper(), p2_name.upper()], [p1_data[metric].mean(), p2_data[metric].mean()], [COLORS['RED'], COLORS['BLACK']]
    if team_data is not None and not team_data.empty:
        names.append('TAKIM ORT.'); values.append(team_data[metric].mean()); colors.append(COLORS['GRAY_500'])

    m_info = METRICS.get(metric, {'display': metric, 'unit': ''})
    fig = go.Figure(go.Bar(
        x=names, y=values, marker=dict(color=colors),
        text=[f"{v:.1f}" for v in values], textposition='outside', textfont=dict(family=_FONT, size=12, weight='bold')
    ))
    layout = _base_layout(m_info['display'].upper(), height=360)
    layout.update(showlegend=False, yaxis=dict(title=m_info['unit']))
    fig.update_layout(**layout)
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# PDF OLUŞTURUCU VE RAPOR HTML ŞABLONU
# ─────────────────────────────────────────────────────────────────────────────

def generate_pdf_from_html(html_content: str):
    try:
        from xhtml2pdf import pisa
        from io import BytesIO
        result = BytesIO()
        pisa_status = pisa.CreatePDF(BytesIO(html_content.encode('utf-8')), dest=result, encoding='utf-8')
        if not pisa_status.err:
            return result.getvalue()
        return None
    except ImportError:
        return None

def generate_player_report_html(player_name: str, age_group: str, stats: dict, score_dict: dict, player_data: pd.DataFrame, team_data: pd.DataFrame, camp_name: str = "Kamp Performansı", photo_url: str = "", club_logo_url: str = "") -> str:
    from datetime import datetime
    def pct_bar(pct):
        color = percentile_color(pct)
        return f'<table width="100%" cellpadding="0" cellspacing="0" style="margin: 0;"><tr><td width="70%" style="background-color: #E5E7EB; height: 10px; border-radius: 4px;"><div style="width: {pct}%; height: 10px; background-color: {color}; border-radius: 4px;"></div></td><td width="30%" style="padding-left: 10px; font-size: 12px; font-weight: bold; color: {color};">%{(pct):.0f}</td></tr></table>'

    composite = score_dict.get('composite', 0)
    comp_color = percentile_color(composite)

    metric_rows = ""
    for m in PRIMARY_METRICS:
        if m not in player_data.columns: continue
        mi = METRICS.get(m, {'display': m, 'unit': ''})
        pval = player_data[m].dropna().mean()
        tmin = team_data[m].dropna().min() if not team_data.empty else 0
        tavg = team_data[m].dropna().mean() if not team_data.empty else 0
        tmax = team_data[m].dropna().max() if not team_data.empty else 0
        pct = score_dict.get(m, 50)
        
        metric_rows += f'<tr><td style="padding:14px; font-weight:bold; color:#1F2937; border-bottom:1px solid #E5E7EB; text-transform:uppercase;">{mi["display"]}</td><td style="padding:14px; text-align:center; font-weight:bold; color:#E30A17; border-bottom:1px solid #E5E7EB; font-size:13px;">{pval:.1f} <span style="color:#9CA3AF; font-size:9px;">{mi["unit"]}</span></td><td style="padding:14px; text-align:center; color:#6B7280; font-weight:bold; border-bottom:1px solid #E5E7EB;">{tmin:.1f}</td><td style="padding:14px; text-align:center; color:#6B7280; font-weight:bold; border-bottom:1px solid #E5E7EB;">{tavg:.1f}</td><td style="padding:14px; text-align:center; color:#6B7280; font-weight:bold; border-bottom:1px solid #E5E7EB;">{tmax:.1f}</td><td style="padding:14px; border-bottom:1px solid #E5E7EB; width: 150px;">{pct_bar(pct)}</td></tr>'

    return f"""<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><style>@page {{ size: A4 portrait; margin: 1.5cm; }} body {{ font-family: Helvetica, Arial, sans-serif; font-size: 11px; color: #111827; background-color: #FFFFFF; }} .header-table {{ width: 100%; background-color: #111827; border-left: 8px solid #E30A17; margin-bottom: 25px; border-radius: 4px; }} .header-td {{ padding: 25px 30px; }} .h-title {{ color: #FFFFFF; font-size: 32px; font-weight: bold; margin: 0; padding: 0; text-transform: uppercase; letter-spacing: 2px; }} .h-sub {{ color: #D1D5DB; font-size: 12px; margin-top: 5px; font-weight: bold; letter-spacing: 1px; }} .h-top {{ color: #9CA3AF; font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 5px; font-weight: bold; }} .score-table {{ background-color: #1F2937; border: 3px solid {comp_color}; border-radius: 8px; text-align: center; }} .score-td {{ padding: 15px; }} .score-val {{ color: {comp_color}; font-size: 38px; font-weight: bold; line-height: 1; }} .score-lbl {{ color: #D1D5DB; font-size: 9px; font-weight: bold; text-transform: uppercase; margin-top: 5px; letter-spacing: 1px; }} .section-title {{ font-size: 16px; font-weight: bold; color: #1F2937; border-bottom: 3px solid #E30A17; padding-bottom: 8px; margin-bottom: 20px; margin-top: 15px; text-transform: uppercase; letter-spacing: 1px; display: inline-block; }} .cards-table {{ width: 100%; margin-bottom: 30px; }} .card-td {{ background-color: #F9FAFB; padding: 15px 5px; text-align: center; border: 1px solid #E5E7EB; border-radius: 8px; }} .card-val {{ color: #E30A17; font-size: 24px; font-weight: bold; }} .card-lbl {{ color: #6B7280; font-size: 10px; font-weight: bold; text-transform: uppercase; margin-top: 6px; letter-spacing: 1px; }} .data-table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }} .data-table th {{ background-color: #F3F4F6; padding: 12px 12px; text-align: left; font-size: 10px; font-weight: bold; color: #4B5563; text-transform: uppercase; border-bottom: 2px solid #D1D5DB; letter-spacing: 0.5px; }} .data-table th.center {{ text-align: center; }} .footer {{ text-align: center; font-size: 11px; font-weight: bold; color: #9CA3AF; margin-top: 40px; padding-top: 15px; border-top: 1px solid #E5E7EB; letter-spacing: 0.5px; }}</style></head><body><table class="header-table" cellpadding="0" cellspacing="0"><tr><td width="15%" style="padding: 15px; text-align: center; vertical-align: middle;"><img src="{photo_url}" width="80" height="80" style="border: 3px solid white; border-radius: 8px; margin-bottom: 5px;"><br><img src="{club_logo_url}" width="35" height="35"></td><td class="header-td" width="55%" style="vertical-align: middle;"><div class="h-top">Rugby · ATLETİK PERFORMANS RAPORU</div><div class="h-title">{player_name}</div><div class="h-sub">{age_group} · {camp_name} · {datetime.now().strftime('%d.%m.%Y')}</div></td><td width="30%" align="right" style="padding: 20px; vertical-align: middle;"><table class="score-table" cellpadding="0" cellspacing="0" width="100%"><tr><td class="score-td"><div class="score-val">{composite:.0f}</div><div class="score-lbl">BİLEŞİK PERCENTILE</div></td></tr></table></td></tr></table><div class="section-title">GENEL İSTATİSTİKLER</div><table class="cards-table" cellpadding="0" cellspacing="12"><tr><td class="card-td" width="20%"><div class="card-val">{int(stats.get('camp_count',0))}</div><div class="card-lbl">KAMP SAYISI</div></td><td class="card-td" width="20%"><div class="card-val">{int(stats.get('session_count',0))}</div><div class="card-lbl">KAYITLI GÜN</div></td><td class="card-td" width="20%"><div class="card-val">{int(stats.get('training_count',0))}</div><div class="card-lbl">ANTRENMAN</div></td><td class="card-td" width="20%"><div class="card-val">{int(stats.get('match_count',0))}</div><div class="card-lbl">MAÇ GÜNÜ</div></td><td class="card-td" width="20%"><div class="card-val">{stats.get('max_speed',0):.1f}</div><div class="card-lbl">MAX KM/H</div></td></tr></table><div class="section-title">METRİK BAZLI ANALİZ (MİN / ORT / MAX)</div><table class="data-table"><thead><tr><th>METRİK (DEĞİŞKEN)</th><th class="center">OYUNCU</th><th class="center">TAKIM MİN</th><th class="center">TAKIM ORT.</th><th class="center">TAKIM MAX</th><th>ATLETİK PERFORMANS SKORLAMASI</th></tr></thead><tbody>{metric_rows}</tbody></table><div class="footer">Rugby Performans Sistemi · Genç Takımlar Atletik Performans Sistemi · © {datetime.now().year} TFF</div></body></html>"""


# ─────────────────────────────────────────────────────────────────────────────
# EXPORT BUTONLARI
# ─────────────────────────────────────────────────────────────────────────────

def render_export_buttons(fig=None, df=None, html_report=None, key_prefix='export', filename='tff'):
    import streamlit as st
    
    safe_filename = re.sub(r'[^\w\s-]', '', filename).strip()
    cols = st.columns(6)

    if fig is not None:
        with cols[0]:
            try:
                data = fig.to_image(format='png', width=1400, height=700, scale=2)
                st.download_button("📷 PNG İNDİR", data, f"{safe_filename}.png", "image/png", key=f"{key_prefix}_png", width='stretch')
            except Exception:
                st.button("❌ PNG HATASI", disabled=True, key=f"{key_prefix}_png_err", help="Sisteminizde 'kaleido' paketi eksik olabilir.", width='stretch')
                
        with cols[1]:
            data = fig.to_html(full_html=True, include_plotlyjs='cdn').encode('utf-8')
            st.download_button("🌐 İNTERAKTİF HTML", data, f"{safe_filename}.html", "text/html", key=f"{key_prefix}_html", width='stretch')

    if df is not None:
        with cols[2]:
            data = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📊 EXCEL (CSV)", data, f"{safe_filename}.csv", "text/csv", key=f"{key_prefix}_csv", width='stretch')

    if html_report is not None:
        with cols[3]:
            data_html = html_report.encode('utf-8')
            st.download_button("📄 RAPOR (HTML)", data_html, f"{safe_filename}.html", "text/html", key=f"{key_prefix}_rhtml", width='stretch')
        with cols[4]:
            try:
                pdf_data = generate_pdf_from_html(html_report)
                if pdf_data:
                    st.download_button("📕 RAPOR (PDF)", pdf_data, f"{safe_filename}.pdf", "application/pdf", key=f"{key_prefix}_rpdf", width='stretch')
                else:
                    st.button("❌ PDF HATASI", disabled=True, key=f"{key_prefix}_pdf_err", width='stretch')
            except ImportError:
                st.button("❌ PDF HATASI", disabled=True, key=f"{key_prefix}_pdf_err_2", help="xhtml2pdf paketi eksik.", width='stretch')

                # utils.py dosyasının en altına eklenecek kısım

def calculate_per90_stats(df, metrics_to_normalize):
    """
    Verileri 90 dakikaya normalize eder ve Yoğunluk İndekslerini hesaplar.
    """
    d = df.copy()
    # 0 dakikaları ele (Division by zero hatası için)
    d = d[d['minutes'] > 0].copy()
    
    # 1. Per 90 Normalizasyonu
    for m in metrics_to_normalize:
        if m in d.columns:
            d[f'{m}_p90'] = (d[m] / d['minutes']) * 90

    # 2. Atletik Verimlilik İndeksi (AEI): Mesafe / Player Load
    # Oyuncu harcadığı her birim yükte ne kadar mesafe kat ediyor?
    if 'total_distance' in d.columns and 'player_load' in d.columns:
        d['verimlilik_indeksi'] = d['total_distance'] / d['player_load']

    # 3. Yoğunluk Skoru (Z-Score tabanlı)
    # Patlayıcılık ve Yoğunluğu harmanlayıp 0-100 arası bir puan verir
    if 'dist_25_plus_p90' in d.columns and 'total_distance_p90' in d.columns:
        # Basit bir verimlilik ağırlıklandırması
        d['atletik_puan'] = (
            (d['dist_25_plus_p90'] / d['dist_25_plus_p90'].max() * 0.4) +
            (d['total_distance_p90'] / d['total_distance_p90'].max() * 0.3) +
            (d['smax_kmh'] / d['smax_kmh'].max() * 0.3)
        ) * 100

    return d.round(2)

def get_hierarchical_top_players(df):
    """
    Hiyerarşik olarak (Seans, Kamp, Genel) en iyi oyuncuları belirler.
    """
    per90_df = calculate_per90_stats(df, ['total_distance', 'dist_25_plus', 'player_load'])
    
    hierarchy = {
        "GÜNÜN_KRALI": per90_df.sort_values('atletik_puan', ascending=False).iloc[0].to_dict(),
        "KAMPIN_MOTORU": per90_df.groupby('player_name')['atletik_puan'].mean().sort_values(ascending=False).head(3).to_dict(),
        "ISTIKRAR_ABIDESI": (1 / (per90_df.groupby('player_name')['atletik_puan'].std() / per90_df.groupby('player_name')['atletik_puan'].mean())).sort_values(ascending=False).head(3).to_dict()
    }
    return hierarchy