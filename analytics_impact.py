"""
Rugby Performans Sistemi - Impact Score Model
Günlük ve kamp bazlı fiziksel performans analizi
Karar destek sistemi için oyuncu etkililiği skorlaması
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from datetime import datetime
from config import COLORS

# ─────────────────────────────────────────────────────────────────────────────
# IMPACT SCORE PARAMETRELERI
# ─────────────────────────────────────────────────────────────────────────────

IMPACT_WEIGHTS = {
    'high_speed': 0.25,      # distance > 25 km/h
    'explosive': 0.20,       # acceleration + deceleration
    'load': 0.20,            # player load intensity
    'volume': 0.15,          # total distance
    'max_velocity': 0.10,    # smax
    'metabolic': 0.10        # AMP / metrage
}

IMPACT_THRESHOLDS = {
    'high_impact_sigma': 1.0,     # 1 std üstü "High Impact"
    'match_ready_high_speed': 0.7,
    'match_ready_load': 0.6,
    'finisher_volume': -0.3,      # düşük volume
    'finisher_high_speed': 0.5,   # yüksek high speed
    'load_risk_threshold': 0.8,   # yüksek load
    'elite_percentile': 75         # En iyi %25
}

# ─────────────────────────────────────────────────────────────────────────────
# 1. VERİ STANDARDIZASYONU (Per Minute & Z-Score)
# ─────────────────────────────────────────────────────────────────────────────

def normalize_per_minute(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tüm metrikleri dakika başına normalize et
    
    Args:
        df: performance_data DataFrame
        
    Returns:
        pd.DataFrame: Normalized metrics eklenen dataframe
    """
    df = df.copy()
    
    # Per minute metrikleri hesapla
    metrics_to_normalize = [
        'total_distance', 'metrage', 'dist_20_25', 'dist_25_plus',
        'dist_acc_3', 'dist_dec_3', 'n_20_25', 'n_25_plus',
        'player_load', 'amp'
    ]
    
    for metric in metrics_to_normalize:
        if metric in df.columns:
            # minutes = 0 ise NaN yap (bölme hatasını önle)
            df[f'{metric}_pm'] = df.apply(
                lambda row: (row[metric] / row['minutes'] * 90) 
                if row['minutes'] > 0 else np.nan,
                axis=1
            )
    
    return df


def calculate_z_scores_by_group(df: pd.DataFrame, 
                                group_cols: List[str],
                                metric_cols: List[str]) -> pd.DataFrame:
    """
    Grup içinde z-score hesapla (aynı gün + aynı kamp)
    
    Args:
        df: DataFrame with normalized metrics
        group_cols: Grouping columns ['tarih', 'camp_id', 'tip']
        metric_cols: Metrics to calculate z-scores for
        
    Returns:
        pd.DataFrame: Z-score columns eklenen dataframe
    """
    df = df.copy()
    
    for metric in metric_cols:
        if f'{metric}_pm' in df.columns:
            # Her grup için mean ve std hesapla
            grouped = df.groupby(group_cols)[f'{metric}_pm'].transform(
                lambda x: (x - x.mean()) / (x.std() + 1e-6)
            )
            df[f'{metric}_z'] = grouped
    
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 2. IMPACT SCORE HESAPLAMA
# ─────────────────────────────────────────────────────────────────────────────

def calculate_daily_impact_score(df: pd.DataFrame, 
                                 session_type: str = 'ALL') -> pd.DataFrame:
    """
    Günlük Impact Score hesapla
    
    Bileşenler:
    - High Speed Index: distance > 25 per minute
    - Explosive Index: (acceleration + deceleration) per minute
    - Load Intensity: player load per minute
    - Volume Index: total distance per minute
    - Max Velocity: smax per game
    - Metabolic: AMP per minute
    
    Args:
        df: DataFrame with z-scores
        session_type: 'TRAINING', 'MATCH', 'ALL'
        
    Returns:
        pd.DataFrame: impact_score column eklenen dataframe
    """
    df = df.copy()
    
    # Filtrele
    if session_type == 'TRAINING':
        mask = df['tip'].str.upper().str.contains('TRAINING', na=False)
        df = df[mask].copy()
    elif session_type == 'MATCH':
        mask = df['tip'].str.upper().str.contains('MATCH', na=False)
        df = df[mask].copy()
    
    # Her bileşen z-score'dan oluştur
    impact_components = pd.DataFrame(index=df.index)
    
    # 1. High Speed Index
    if 'dist_25_plus_z' in df.columns:
        impact_components['high_speed'] = df['dist_25_plus_z'].fillna(0)
    else:
        impact_components['high_speed'] = 0.0
    
    # 2. Explosive Index (acceleration + deceleration)
    if 'dist_acc_3_z' in df.columns and 'dist_dec_3_z' in df.columns:
        explosive = (df['dist_acc_3_z'].fillna(0) + df['dist_dec_3_z'].fillna(0)) / 2
        impact_components['explosive'] = explosive
    else:
        impact_components['explosive'] = 0.0
    
    # 3. Load Intensity
    if 'player_load_z' in df.columns:
        impact_components['load'] = df['player_load_z'].fillna(0)
    else:
        impact_components['load'] = 0.0
    
    # 4. Volume Index
    if 'total_distance_z' in df.columns:
        impact_components['volume'] = df['total_distance_z'].fillna(0)
    else:
        impact_components['volume'] = 0.0
    
    # 5. Max Velocity
    if 'smax_kmh' in df.columns:
        # smax'i z-score'a çevir (sadece bu grup için)
        smax_mean = df['smax_kmh'].mean()
        smax_std = df['smax_kmh'].std()
        impact_components['max_velocity'] = (
            (df['smax_kmh'] - smax_mean) / (smax_std + 1e-6)
        ).fillna(0)
    else:
        impact_components['max_velocity'] = 0.0
    
    # 6. Metabolic Power
    if 'amp_z' in df.columns:
        impact_components['metabolic'] = df['amp_z'].fillna(0)
    else:
        impact_components['metabolic'] = 0.0
    
    # Ağırlıklı toplam
    impact_score = (
        impact_components['high_speed'] * IMPACT_WEIGHTS['high_speed'] +
        impact_components['explosive'] * IMPACT_WEIGHTS['explosive'] +
        impact_components['load'] * IMPACT_WEIGHTS['load'] +
        impact_components['volume'] * IMPACT_WEIGHTS['volume'] +
        impact_components['max_velocity'] * IMPACT_WEIGHTS['max_velocity'] +
        impact_components['metabolic'] * IMPACT_WEIGHTS['metabolic']
    )
    
    # 0-100 ölçeğine dönüştür
    impact_min = impact_score.min()
    impact_max = impact_score.max()
    impact_range = impact_max - impact_min
    
    if impact_range > 0:
        df['impact_score'] = ((impact_score - impact_min) / impact_range * 100)
    else:
        df['impact_score'] = 50.0
    
    df['impact_components'] = impact_components.to_dict('records')
    
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 3. GÜNLÜK FARK YARATAN OYUNCULAR
# ─────────────────────────────────────────────────────────────────────────────

def identify_daily_top_performers(df: pd.DataFrame, 
                                  camp_id: int,
                                  tarih: str,
                                  top_n: int = 3) -> Dict:
    """
    Günün en etkili oyuncularını tespit et
    
    Args:
        df: DataFrame with impact_score
        camp_id: Kamp ID
        tarih: Tarih
        top_n: Kaç oyuncu gösterilecek
        
    Returns:
        Dict: Top performers ve impact seviyesi
    """
    day_data = df[
        (df['camp_id'] == camp_id) & 
        (df['tarih'] == tarih)
    ].copy()
    
    if day_data.empty:
        return {'top_performers': [], 'high_impact_players': []}
    
    day_data = day_data.sort_values('impact_score', ascending=False)
    
    # Group istatistikleri
    group_mean = day_data['impact_score'].mean()
    group_std = day_data['impact_score'].std()
    
    result = {
        'top_performers': day_data.head(top_n)[
            ['player_name', 'impact_score', 'tip']
        ].to_dict('records'),
        'high_impact_players': day_data[
            day_data['impact_score'] > (group_mean + group_std * IMPACT_THRESHOLDS['high_impact_sigma'])
        ][['player_name', 'impact_score']].to_dict('records'),
        'group_mean': group_mean,
        'group_std': group_std,
        'total_players': len(day_data)
    }
    
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 4. KAMP BAZLI IMPACT ANALİZİ
# ─────────────────────────────────────────────────────────────────────────────

def calculate_camp_impact_summary(df: pd.DataFrame, camp_id: int) -> pd.DataFrame:
    """
    Kamp boyunca her oyuncunun ortalama Impact Score'unu hesapla
    
    Args:
        df: DataFrame with impact_score
        camp_id: Kamp ID
        
    Returns:
        pd.DataFrame: Camp impact summary
    """
    camp_data = df[df['camp_id'] == camp_id].copy()
    
    summary = camp_data.groupby('player_name').agg({
        'impact_score': ['mean', 'std', 'min', 'max', 'count'],
        'total_distance': 'mean',
        'dist_25_plus': 'mean',
        'player_load': 'mean',
        'smax_kmh': 'max',
        'age_group': 'first'
    }).round(2)
    
    summary.columns = [
        'avg_impact', 'std_impact', 'min_impact', 'max_impact', 'session_count',
        'avg_distance', 'avg_high_speed', 'avg_load', 'max_speed', 'age_group'
    ]
    
    summary = summary.sort_values('avg_impact', ascending=False)
    summary['rank'] = range(1, len(summary) + 1)
    
    return summary.reset_index()


# ─────────────────────────────────────────────────────────────────────────────
# 5. GEÇMİŞ KAMPLARLA KARŞILAŞTIRMA (DEVELOPMENT ANALYSIS)
# ─────────────────────────────────────────────────────────────────────────────

def calculate_development_metrics(current_camp_data: pd.DataFrame,
                                  all_data: pd.DataFrame,
                                  player_name: str,
                                  camp_id: int) -> Dict:
    """
    Oyuncunun mevcut kamp performansını geçmiş kamplara göre karşılaştır
    
    Args:
        current_camp_data: Mevcut kamp verisi
        all_data: Tüm veriler
        player_name: Oyuncu adı
        camp_id: Mevcut kamp ID
        
    Returns:
        Dict: Yüzdesel gelişim metrikleri
    """
    # Mevcut kamp ortalaması
    current_camp = current_camp_data[
        current_camp_data['player_name'] == player_name
    ]
    
    if current_camp.empty:
        return {}
    
    current_metrics = {
        'impact_score': current_camp['impact_score'].mean(),
        'high_speed': current_camp['dist_25_plus'].mean(),
        'explosive': (current_camp['dist_acc_3'].fillna(0) + 
                     current_camp['dist_dec_3'].fillna(0)).mean() / 2,
        'load': current_camp['player_load'].mean(),
        'volume': current_camp['total_distance'].mean(),
    }
    
    # Geçmiş kamplardaki aynı oyuncu
    player_history = all_data[
        (all_data['player_name'] == player_name) &
        (all_data['camp_id'] != camp_id)  # Mevcut kamp hariç
    ]
    
    if player_history.empty:
        return {'current': current_metrics, 'comparison': {}}
    
    previous_metrics = {
        'impact_score': player_history['impact_score'].mean() if 'impact_score' in player_history.columns else 50,
        'high_speed': player_history['dist_25_plus'].mean(),
        'explosive': (player_history['dist_acc_3'].fillna(0) + 
                     player_history['dist_dec_3'].fillna(0)).mean() / 2,
        'load': player_history['player_load'].mean(),
        'volume': player_history['total_distance'].mean(),
    }
    
    # Yüzdesel değişim hesapla
    development = {}
    for metric in current_metrics.keys():
        if previous_metrics[metric] > 0:
            change = (
                (current_metrics[metric] - previous_metrics[metric]) / 
                previous_metrics[metric] * 100
            )
        else:
            change = 0
        
        development[metric] = {
            'current': round(current_metrics[metric], 2),
            'previous': round(previous_metrics[metric], 2),
            'change_percent': round(change, 1),
            'comparison_count': len(player_history['camp_id'].unique())
        }
    
    return development


# ─────────────────────────────────────────────────────────────────────────────
# 6. RENK KODLAMA
# ─────────────────────────────────────────────────────────────────────────────

def get_development_color(change_percent: float) -> str:
    """Yüzdesel değişime göre renk dönüş"""
    if change_percent >= 10:
        return '#059669'  # Koyu yeşil - Önemli gelişim
    elif change_percent >= 5:
        return '#10B981'  # Açık yeşil - Pozitif trend
    elif change_percent >= -5:
        return '#FBBF24'  # Sarı - Stabil
    elif change_percent >= -10:
        return '#F97316'  # Turuncu - Düşüş
    else:
        return '#DC2626'  # Kırmızı - Kritik düşüş


def get_impact_color(impact_score: float, group_mean: float = 50, 
                     group_std: float = 15) -> str:
    """Impact Score'a göre renk dönüş"""
    if impact_score > (group_mean + group_std):
        return '#059669'  # Yeşil - Üstün
    elif impact_score > group_mean:
        return '#10B981'  # Açık yeşil - İyi
    elif impact_score > (group_mean - group_std):
        return '#FBBF24'  # Sarı - Orta
    elif impact_score > (group_mean - 2 * group_std):
        return '#F97316'  # Turuncu - Düşük
    else:
        return '#DC2626'  # Kırmızı - Çok düşük


# ─────────────────────────────────────────────────────────────────────────────
# 7. TREND ANALİZİ
# ─────────────────────────────────────────────────────────────────────────────

def calculate_trend_analysis(camp_data: pd.DataFrame, 
                             player_name: str) -> Dict:
    """
    Kamp içindeki gün gün trend analizi
    
    Args:
        camp_data: Kamp verisi
        player_name: Oyuncu adı
        
    Returns:
        Dict: Trend metrikleri
    """
    player_data = camp_data[
        camp_data['player_name'] == player_name
    ].sort_values('tarih')
    
    if len(player_data) < 2:
        return {'status': 'insufficient_data'}
    
    # İlk gün vs son gün
    first_day = player_data.iloc[0]
    last_day = player_data.iloc[-1]
    
    metrics_to_track = [
        'total_distance', 'dist_25_plus', 'player_load', 'smax_kmh'
    ]
    
    trend = {}
    for metric in metrics_to_track:
        if metric in player_data.columns:
            first_val = first_day[metric]
            last_val = last_day[metric]
            
            if first_val > 0:
                change = ((last_val - first_val) / first_val) * 100
            else:
                change = 0
            
            trend[metric] = {
                'first': round(first_val, 2),
                'last': round(last_val, 2),
                'change': round(change, 1)
            }
    
    # Trend durumu
    avg_change = np.mean([t['change'] for t in trend.values()])
    if avg_change > 5:
        trend['status'] = 'IMPROVING'
    elif avg_change < -5:
        trend['status'] = 'DECLINING'
    else:
        trend['status'] = 'STABLE'
    
    return trend


# ─────────────────────────────────────────────────────────────────────────────
# 8. ROL BAZLI OYUNCU KATEGORİZASYONU
# ─────────────────────────────────────────────────────────────────────────────

def classify_player_profile(player_impact_data: pd.DataFrame) -> Dict:
    """
    Oyuncuyu rol-bazlı kategorilere ayırır
    
    Kategoriler:
    - Match Ready: Yüksek intensity + yüksek high speed
    - Finisher Profile: Düşük volume + yüksek high speed
    - Load Risk: Yüksek load + düşen high speed
    - High Impact Player: Kampın en etkili oyuncuları
    
    Args:
        player_impact_data: Oyuncunun tüm kamp verisi
        
    Returns:
        Dict: Rol kategorileri
    """
    if player_impact_data.empty:
        return {}
    
    # Ortalamalar
    avg_impact = player_impact_data['impact_score'].mean()
    avg_high_speed = player_impact_data['dist_25_plus'].mean()
    avg_load = player_impact_data['player_load'].mean()
    avg_volume = player_impact_data['total_distance'].mean()
    
    # Standartlaştır (0-1)
    camp_high_speed_mean = player_impact_data['dist_25_plus'].mean()
    camp_high_speed_std = player_impact_data['dist_25_plus'].std()
    high_speed_normalized = (
        (avg_high_speed - camp_high_speed_mean) / (camp_high_speed_std + 1e-6)
    )
    
    camp_load_mean = player_impact_data['player_load'].mean()
    camp_load_std = player_impact_data['player_load'].std()
    load_normalized = (
        (avg_load - camp_load_mean) / (camp_load_std + 1e-6)
    )
    
    camp_volume_mean = player_impact_data['total_distance'].mean()
    camp_volume_std = player_impact_data['total_distance'].std()
    volume_normalized = (
        (avg_volume - camp_volume_mean) / (camp_volume_std + 1e-6)
    )
    
    # Kategorilendirme
    profiles = {
        'match_ready': (
            high_speed_normalized > IMPACT_THRESHOLDS['match_ready_high_speed'] and
            load_normalized > IMPACT_THRESHOLDS['match_ready_load']
        ),
        'finisher': (
            volume_normalized < IMPACT_THRESHOLDS['finisher_volume'] and
            high_speed_normalized > IMPACT_THRESHOLDS['finisher_high_speed']
        ),
        'load_risk': (
            load_normalized > IMPACT_THRESHOLDS['load_risk_threshold'] and
            high_speed_normalized < 0
        ),
        'high_impact': avg_impact > 60
    }
    
    return {
        'primary_profile': max(profiles.items(), key=lambda x: x[1])[0] if any(profiles.values()) else 'balanced',
        'profiles': profiles,
        'metrics': {
            'impact': round(avg_impact, 1),
            'high_speed': round(avg_high_speed, 1),
            'load': round(avg_load, 1),
            'volume': round(avg_volume, 1)
        }
    }


# ─────────────────────────────────────────────────────────────────────────────
# 9. KARAR DESTEK ÖZET
# ─────────────────────────────────────────────────────────────────────────────

def generate_decision_support_summary(camp_data: pd.DataFrame) -> Dict:
    """
    Teknik ekip kararlarını destekleyecek otomatik özet
    
    Args:
        camp_data: Kamp verisi
        
    Returns:
        Dict: Karar destek metrikleri
    """
    summary = {
        'date_generated': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'most_impactful_players': [],
        'match_ready_players': [],
        'load_risk_players': [],
        'most_improved_players': [],
        'declining_performance_players': []
    }
    
    # En etkili oyuncular
    camp_impact = calculate_camp_impact_summary(camp_data, camp_data['camp_id'].iloc[0])
    summary['most_impactful_players'] = camp_impact.head(5)[
        ['player_name', 'avg_impact', 'session_count']
    ].to_dict('records')
    
    # Maç oynamaya hazır oyuncular
    for player in camp_data['player_name'].unique():
        player_data = camp_data[camp_data['player_name'] == player]
        profile = classify_player_profile(player_data)
        
        if profile.get('profiles', {}).get('match_ready', False):
            summary['match_ready_players'].append({
                'player': player,
                'impact': profile['metrics']['impact']
            })
        
        if profile.get('profiles', {}).get('load_risk', False):
            summary['load_risk_players'].append({
                'player': player,
                'load': profile['metrics']['load']
            })
    
    return summary