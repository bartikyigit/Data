# Bursaspor Veri Merkezi - Konfigürasyon v5.0

AGE_GROUPS = ['A Takım', 'U19', 'U17', 'U16', 'U15', 'U14', '_']

DATE_FORMAT    = '%d.%m.%Y'
DATE_FORMAT_DB = '%Y-%m-%d'

DATAFRAME_KWARGS = {'use_container_width': True, 'hide_index': True}

# ─── Metrik tanımları (Bursaspor GPS Standartları) ───────────────────────────
METRICS_BASE = {
    'minutes':        {'display': 'Dakika',                  'unit': 'dk',   'group': 'A', 'icon': '⏱'},
    'total_distance': {'display': 'Toplam Mesafe',           'unit': 'm',    'group': 'A', 'icon': '📏'},
    'metrage':        {'display': 'Metraj',                  'unit': 'm',    'group': 'A', 'icon': '🔥'},
    'dist_20_25':     {'display': 'Mesafe 20-25 km/h (HSR)','unit': 'm',    'group': 'A', 'icon': '💨'},
    'dist_25_plus':   {'display': 'Mesafe 25+ km/h (Sprint)','unit': 'm',    'group': 'A', 'icon': '⚡'},
    'smax_kmh':       {'display': 'Maksimum Hız',            'unit': 'km/h', 'group': 'A', 'icon': '🚀'},
    'player_load':    {'display': 'Oyuncu Yükü (Load)',      'unit': '',     'group': 'A', 'icon': '💪'},
    'amp':            {'display': 'AMP',                     'unit': '',     'group': 'A', 'icon': '📊'},
}

METRICS_ACC_DEC = {
    'dist_acc_3':     {'display': 'İvmelenme > 3 m/s²',      'unit': 'm', 'group': 'B', 'icon': '▲'},
    'dist_dec_3':     {'display': 'Yavaşlama < -3 m/s²',     'unit': 'm', 'group': 'B', 'icon': '▼'},
}

METRICS_N = {
    'n_20_25':        {'display': 'Koşu Sayısı 20-25 km/h',  'unit': 'n', 'group': 'C', 'icon': '🏃'},
    'n_25_plus':      {'display': 'Sprint Sayısı 25+',       'unit': 'n', 'group': 'C', 'icon': '🏃'},
}

METRICS = {**METRICS_BASE, **METRICS_ACC_DEC, **METRICS_N}

# ─── Bileşik skor metrikleri ─────────────────────────────────────────────────
PRIMARY_METRICS = [
    'total_distance', 'metrage', 'dist_20_25', 'dist_25_plus',
    'smax_kmh', 'player_load', 'amp', 'dist_acc_3', 'dist_dec_3',
    'n_20_25', 'n_25_plus'
]

# ─── Metrik ağırlıkları ──────────────────────────────────────────────────────
METRIC_WEIGHTS = {
    'total_distance': 1.0,
    'metrage':        1.0,
    'dist_20_25':     1.0,
    'dist_25_plus':   1.0,
    'smax_kmh':       1.0,
    'player_load':    1.0,
    'amp':            1.0,
    'dist_acc_3':     1.0,
    'dist_dec_3':     1.0,
    'n_20_25':        1.0,
    'n_25_plus':      1.0,
}

RADAR_METRICS = PRIMARY_METRICS.copy()

SCATTER_PRESETS = [
    ('total_distance', 'smax_kmh'),
    ('total_distance', 'player_load'),
    ('metrage',        'dist_25_plus'),
    ('dist_20_25',     'dist_25_plus'),
    ('player_load',    'amp'),
]

# ─── Çoklu oyuncu grafik paleti (Bursaspor Uyarlaması) ────────────────────────
PLAYER_PALETTE = ['#007A33', '#0D0D0D', '#374151', '#2563EB', '#D97706', '#7C3AED']

# ─── Renk Paleti (Bursaspor Kurumsal) ────────────────────────────────────────
COLORS = {
    # Marka (Bursaspor)
    'GREEN':        '#007A33',
    'GREEN_DARK':   '#005C26',
    'GREEN_LIGHT':  '#E6F2EB',
    'GREEN_MID':    'rgba(0,122,51,0.12)',
    'BLACK':        '#0D0D0D',
    # Gri skalası
    'GRAY_900':     '#111827',
    'GRAY_800':     '#1F2937',
    'GRAY_700':     '#374151',
    'GRAY_600':     '#4B5563',
    'GRAY_500':     '#6B7280',
    'GRAY_400':     '#9CA3AF',
    'GRAY_300':     '#D1D5DB',
    'GRAY_200':     '#E5E7EB',
    'GRAY_100':     '#F3F4F6',
    'GRAY_50':      '#F9FAFB',
    'WHITE':        '#FFFFFF',
    # Durum
    'SUCCESS':      '#059669',
    'WARNING':      '#D97706',
    'DANGER':       '#DC2626',
    'INFO':         '#2563EB',
    # Grafik
    'TRAINING':     '#007A33',
    'MATCH':        '#0D0D0D',
    'TEAM_AVG':     '#6B7280',
    'BAND_FILL':    'rgba(107,114,128,0.12)',
    # Karşılaştırma
    'WIN':          '#059669',
    'LOSS':         '#DC2626',
    'TIE':          '#D97706',
    # Percentile seviyeleri
    'EXCELLENT':    '#059669',
    'GOOD':         '#2563EB',
    'MEDIUM':       '#D97706',
    'LOW':          '#DC2626',
}

# ─── Pozisyonlar (Futbol Mevkileri) ──────────────────────────────────────────
POSITIONS = {
    'GK':  {'display': 'Kaleci',        'short': 'KL',  'color': '#F59E0B'},
    'CB':  {'display': 'Stoper',        'short': 'ST',  'color': '#3B82F6'},
    'LB':  {'display': 'Sol Bek',       'short': 'SB',  'color': '#3B82F6'},
    'RB':  {'display': 'Sağ Bek',       'short': 'SğB', 'color': '#3B82F6'},
    'DM':  {'display': 'Defansif Orta', 'short': 'DO',  'color': '#8B5CF6'},
    'CM':  {'display': 'Orta Saha',     'short': 'OS',  'color': '#8B5CF6'},
    'LM':  {'display': 'Sol Kanat',     'short': 'SK',  'color': '#EC4899'},
    'RM':  {'display': 'Sağ Kanat',     'short': 'SğK', 'color': '#EC4899'},
    'AM':  {'display': 'Ofansif Orta',  'short': 'OO',  'color': '#EC4899'},
    'LW':  {'display': 'Sol Açık',      'short': 'SA',  'color': '#10B981'},
    'RW':  {'display': 'Sağ Açık',      'short': 'SğA', 'color': '#10B981'},
    'CF':  {'display': 'Santrafor',     'short': 'SF',  'color': '#EF4444'},
    'SS':  {'display': 'İkinci Forvet', 'short': 'İF',  'color': '#EF4444'},
}
POSITION_LIST = list(POSITIONS.keys())

# ─── Performans eşik değerleri ───────────────────────────────────────────────
THRESHOLDS = {
    'anomaly_z':        2.5,
    'trend_min_days':   3,
    'elite_percentile': 80,
    'good_percentile':  65,
    'avg_percentile':   50,
    'smax_elite':       31.0,
    'smax_good':        28.0,
    'total_dist_match': 9500,
}

# Futbol normlarına göre güncellendi
DEFAULT_MINUTES = {
    'TRAINING': 60,
    'MATCH': 90
}

ALL_DB_COLUMNS = [
    'minutes', 'total_distance', 'metrage', 'dist_20_25', 'dist_25_plus',
    'dist_acc_3', 'dist_dec_3', 'n_20_25', 'n_25_plus',
    'smax_kmh', 'player_load', 'amp',
]

# ─── IMPACT SCORE MODEL ───────────────────────────────────────────────────────
IMPACT_WEIGHTS = {
    'high_speed': 0.25,
    'explosive': 0.20,
    'load': 0.20,
    'volume': 0.15,
    'max_velocity': 0.10,
    'metabolic': 0.10
}

IMPACT_THRESHOLDS = {
    'high_impact_sigma': 1.0,
    'match_ready_high_speed': 0.7,
    'match_ready_load': 0.6,
    'finisher_volume': -0.3,
    'finisher_high_speed': 0.5,
    'load_risk_threshold': 0.8,
    'elite_percentile': 75
}

DEVELOPMENT_COLOR_THRESHOLDS = {
    'excellent': 10,
    'good': 5,
    'stable_low': -5,
    'declining': -10,
    'critical': -10,
}

IMPACT_COLORS = {
    'excellent_growth': '#059669',
    'good_growth': '#10B981',
    'stable': '#FBBF24',
    'declining': '#F97316',
    'critical': '#DC2626',
}