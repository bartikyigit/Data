"""
Rugby Performans Sistemi — Analytics Engine v2.0
scipy bağımlılığı yok; sadece numpy + pandas.

Yeni özellikler:
  - Ağırlıklı bileşik skor (METRIC_WEIGHTS - Artık tüm metrikler eşit ağırlıkta)
  - OLS trend (numpy.polyfit) — scipy.linregress yerine
  - Korelasyon matrisi
  - Form analizi (son N gün)
  - Fatigue index (yük birikimi)
  - Peer comparison (yaş grubu içi karşılaştırma)
  - Session load spike tespiti
"""

import pandas as pd
import numpy as np
from config import PRIMARY_METRICS, METRIC_WEIGHTS, THRESHOLDS, COLORS


# ─────────────────────────────────────────────────────────────────────────────
# TEMEL İSTATİSTİK
# ─────────────────────────────────────────────────────────────────────────────

class AnalyticsEngine:

    # ── Percentile Rank ──────────────────────────────────────────────────────
    @staticmethod
    def calculate_percentile(player_value, team_values: pd.Series) -> float:
        """
        Oyuncunun tek bir metrikte takım içindeki yüzdelik dilimi.
        scipy gerektirmez — saf numpy.
        Dönüş: 0–100 arası float.
        """
        if pd.isna(player_value):
            return 50.0
        valid = team_values.dropna().values
        if len(valid) == 0:
            return 50.0
        n_less  = np.sum(valid < player_value)
        n_equal = np.sum(valid == player_value)
        pct = (n_less + 0.5 * n_equal) / len(valid) * 100
        return float(np.clip(pct, 0, 100))

    # ── Z-Score ──────────────────────────────────────────────────────────────
    @staticmethod
    def calculate_zscore(player_value, team_values: pd.Series) -> float:
        """Standart z-skoru. Sıfır std durumunda 0 döner."""
        if pd.isna(player_value):
            return 0.0
        valid = team_values.dropna()
        if len(valid) < 2:
            return 0.0
        mean = float(valid.mean())
        std  = float(valid.std(ddof=1))
        return 0.0 if std == 0 else (player_value - mean) / std

    # ── Ağırlıklı Bileşik Skor ───────────────────────────────────────────────
    @staticmethod
    def calculate_composite_score(player_data: pd.DataFrame,
                                   team_data: pd.DataFrame,
                                   metrics: list = None,
                                   session_filter: str = "ALL") -> dict:
        """
        Her metrik için percentile hesaplar, METRIC_WEIGHTS ile ağırlıklandırır
        ve bileşik skor üretir.

        session_filter: "ALL" | "TRAINING" | "MATCH"
        Dönüş: {metric: percentile, ..., 'composite': float}
        """
        if metrics is None:
            metrics = PRIMARY_METRICS

        def _filter(df):
            if session_filter == "TRAINING":
                return df[df['tip'].str.upper() == 'TRAINING']
            if session_filter == "MATCH":
                return df[df['tip'].str.upper() == 'MATCH']
            return df

        p  = _filter(player_data)
        td = _filter(team_data)

        scores      = {}
        weights_used = []

        for m in metrics:
            if m not in p.columns or p[m].dropna().empty:
                continue
            if m not in td.columns or td[m].dropna().empty:
                continue

            p_val  = float(p[m].dropna().mean())
            pct    = AnalyticsEngine.calculate_percentile(p_val, td[m])
            w      = METRIC_WEIGHTS.get(m, 1.0)

            scores[m]   = round(pct, 1)
            weights_used.append(w)

        if not scores:
            return {'composite': 50.0}

        # Ağırlıklı ortalama (Artık tüm ağırlıklar 1.0 olduğu için doğrudan eşit ortalama alır)
        total_w   = sum(weights_used)
        ws_list   = [METRIC_WEIGHTS.get(m, 1.0) for m in scores]
        composite = sum(v * w for v, w in zip(scores.values(), ws_list)) / total_w

        scores['composite'] = round(composite, 1)
        return scores

    # ── Anomali Tespiti ───────────────────────────────────────────────────────
    @staticmethod
    def detect_anomalies(data: pd.DataFrame,
                          column: str,
                          z_threshold: float = None) -> pd.Series:
        """
        Z-score tabanlı anomali tespiti.
        z_threshold varsayılan olarak config.THRESHOLDS['anomaly_z'] kullanır.
        Dönüş: boolean Series (True = anomali).
        """
        if z_threshold is None:
            z_threshold = THRESHOLDS['anomaly_z']

        if column not in data.columns:
            return pd.Series([False] * len(data), index=data.index)

        valid = data[column].dropna()
        if len(valid) < 2:
            return pd.Series([False] * len(data), index=data.index)

        mean = float(valid.mean())
        std  = float(valid.std(ddof=1))
        if std == 0:
            return pd.Series([False] * len(data), index=data.index)

        z = np.abs((data[column] - mean) / std)
        return z > z_threshold

    # ── OLS Trend (scipy yerine numpy.polyfit) ────────────────────────────────
    @staticmethod
    def calculate_trend(series: pd.Series) -> tuple:
        """
        Zaman serisine OLS doğru fit eder (numpy.polyfit, derece=1).
        scipy.linregress yerine kullanılır.

        Dönüş: (slope: float, label: str, r_squared: float)
          slope     — günlük değişim miktarı
          label     — Türkçe trend yorumu
          r_squared — fit kalitesi (0–1)
        """
        s = series.dropna()
        n = len(s)

        if n < THRESHOLDS['trend_min_days']:
            return 0.0, "➡️ YETERSİZ VERİ", 0.0

        x = np.arange(n, dtype=float)
        y = s.values.astype(float)

        # Polinom fit (derece 1 = doğrusal)
        coeffs   = np.polyfit(x, y, 1)
        slope    = float(coeffs[0])
        intercept= float(coeffs[1])

        # R² hesabı
        y_pred   = slope * x + intercept
        ss_res   = float(np.sum((y - y_pred) ** 2))
        ss_tot   = float(np.sum((y - y.mean()) ** 2))
        r2       = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Yorum — eğim büyüklüğünü normalize et
        y_range = float(y.max() - y.min()) if y.max() != y.min() else 1.0
        slope_norm = slope / y_range  # -1 ile +1 arası

        if slope_norm > 0.02:
            label = "📈 ARTIŞ TRENDİNDE"
        elif slope_norm < -0.02:
            label = "📉 DÜŞÜŞ TRENDİNDE"
        else:
            label = "➡️ SABİT SEYİR"

        return slope, label, round(r2, 3)

    # ── Çoklu Metrik Trend Özeti ──────────────────────────────────────────────
    @staticmethod
    def calculate_all_trends(player_data: pd.DataFrame,
                              metrics: list = None) -> pd.DataFrame:
        """
        Oyuncunun tüm metrikleri için trend tablosu üretir.
        Dönüş: DataFrame — Metrik | Slope | R² | Trend | İlk | Son | Değişim%
        """
        if metrics is None:
            metrics = PRIMARY_METRICS

        rows = []
        sorted_data = player_data.sort_values('tarih')

        for m in metrics:
            if m not in sorted_data.columns:
                continue
            series = sorted_data[m].dropna()
            if series.empty:
                continue

            slope, label, r2 = AnalyticsEngine.calculate_trend(series)
            first = float(series.iloc[0])
            last  = float(series.iloc[-1])
            change_pct = ((last - first) / first * 100) if first != 0 else 0.0

            from config import METRICS
            m_info = METRICS.get(m, {'display': m, 'unit': ''})
            rows.append({
                'METRİK':    m_info['display'].upper(),
                'BİRİM':     m_info['unit'],
                'EĞİM':      round(slope, 3),
                'R²':        r2,
                'TREND':     label,
                'İLK':       round(first, 1),
                'SON':       round(last, 1),
                'DEĞİŞİM %': round(change_pct, 1),
            })

        return pd.DataFrame(rows)

    # ── Form Analizi (son N gün) ──────────────────────────────────────────────
    @staticmethod
    def calculate_form(player_data: pd.DataFrame,
                        team_data: pd.DataFrame,
                        last_n: int = 5,
                        metrics: list = None) -> dict:
        """
        Son N seansın performansını kamp ortalamasıyla karşılaştırır.

        Dönüş:
          {
            'form_score': float,        # 0–100 — son N seansın bileşik skoru
            'camp_score': float,        # 0–100 — tüm kamp bileşik skoru
            'delta': float,             # form_score - camp_score
            'label': str,               # "🔥 Formda" / "📉 Form Düşüşü" / "➡️ Stabil"
            'metric_deltas': dict       # {metric: {form, camp, delta}}
          }
        """
        if metrics is None:
            metrics = PRIMARY_METRICS

        sorted_p = player_data.sort_values('tarih')
        recent   = sorted_p.tail(last_n)

        form_scores = AnalyticsEngine.calculate_composite_score(recent, team_data, metrics)
        camp_scores = AnalyticsEngine.calculate_composite_score(player_data, team_data, metrics)

        form_c = form_scores.get('composite', 50.0)
        camp_c = camp_scores.get('composite', 50.0)
        delta  = form_c - camp_c

        if delta > 5:
            label = "🔥 FORMDA"
        elif delta < -5:
            label = "📉 FORM DÜŞÜŞÜ"
        else:
            label = "➡️ STABİL"

        metric_deltas = {}
        for m in metrics:
            fv = form_scores.get(m)
            cv = camp_scores.get(m)
            if fv is not None and cv is not None:
                metric_deltas[m] = {
                    'form': fv,
                    'camp': cv,
                    'delta': round(fv - cv, 1),
                }

        return {
            'form_score':    round(form_c, 1),
            'camp_score':    round(camp_c, 1),
            'delta':         round(delta, 1),
            'label':         label,
            'last_n':        last_n,
            'metric_deltas': metric_deltas,
        }

    # ── Fatigue Index (yorgunluk birikimi) ────────────────────────────────────
    @staticmethod
    def calculate_fatigue_index(player_data: pd.DataFrame,
                                 window: int = 3) -> pd.DataFrame:
        """
        Rolling ortalama ile yük birikimi tahmini.
        Yüksek player_load + düşen total_distance → potansiyel yorgunluk sinyali.

        Dönüş: tarih bazlı DataFrame — tarih | load_roll | dist_roll | fatigue_flag
        """
        df = player_data.sort_values('tarih').copy()

        if 'player_load' not in df.columns or 'total_distance' not in df.columns:
            return pd.DataFrame()

        df['load_roll'] = df['player_load'].rolling(window, min_periods=1).mean()
        df['dist_roll'] = df['total_distance'].rolling(window, min_periods=1).mean()

        # Yük yüksek, mesafe düşük → yorgunluk sinyali
        load_high = df['load_roll'] > df['load_roll'].mean() * 1.1
        dist_low  = df['dist_roll'] < df['dist_roll'].mean() * 0.9
        df['fatigue_flag'] = load_high & dist_low

        result = df[['tarih', 'load_roll', 'dist_roll', 'fatigue_flag']].copy()
        result['load_roll'] = result['load_roll'].round(1)
        result['dist_roll'] = result['dist_roll'].round(0)
        return result

    # ── Korelasyon Matrisi ────────────────────────────────────────────────────
    @staticmethod
    def calculate_correlation_matrix(data: pd.DataFrame,
                                      metrics: list = None) -> pd.DataFrame:
        """
        Seçili metriklerin pearson korelasyon matrisi.
        Dönüş: DataFrame (metrik × metrik, değerler -1 ile +1 arası)
        """
        if metrics is None:
            metrics = PRIMARY_METRICS

        avail = [m for m in metrics if m in data.columns and data[m].notna().any()]
        if len(avail) < 2:
            return pd.DataFrame()

        sub = data[avail].dropna()
        if len(sub) < 3:
            return pd.DataFrame()

        # numpy corrcoef
        mat = np.corrcoef(sub.values.T)
        df  = pd.DataFrame(mat, index=avail, columns=avail).round(3)

        # Display isimlerini kullan (Büyük Harf ile)
        from config import METRICS as METRIC_DEF
        rename = {m: METRIC_DEF.get(m, {}).get('display', m).upper() for m in avail}
        df.rename(index=rename, columns=rename, inplace=True)

        return df

    # ── Peer Comparison (oyuncu vs yaş grubu) ────────────────────────────────
    @staticmethod
    def peer_comparison(player_data: pd.DataFrame,
                         age_group_data: pd.DataFrame,
                         metrics: list = None) -> pd.DataFrame:
        """
        Oyuncuyu yaş grubu içindeki tüm oyuncularla karşılaştırır.
        Her metrik için: oyuncu değeri, takım ort, takım std, percentile, z-score.

        Dönüş: DataFrame — her satır bir metrik
        """
        if metrics is None:
            metrics = PRIMARY_METRICS

        rows = []
        from config import METRICS as METRIC_DEF

        for m in metrics:
            if m not in player_data.columns or player_data[m].dropna().empty:
                continue
            if m not in age_group_data.columns:
                continue

            p_val   = float(player_data[m].dropna().mean())
            t_vals  = age_group_data[m].dropna()

            if t_vals.empty:
                continue

            t_mean  = float(t_vals.mean())
            t_std   = float(t_vals.std(ddof=1)) if len(t_vals) > 1 else 0.0
            pct     = AnalyticsEngine.calculate_percentile(p_val, t_vals)
            z       = AnalyticsEngine.calculate_zscore(p_val, t_vals)

            m_info = METRIC_DEF.get(m, {'display': m, 'unit': ''})

            rows.append({
                'METRİK':        m_info['display'].upper(),
                'BİRİM':         m_info['unit'],
                'OYUNCU':        round(p_val, 2),
                'TAKIM ORT.':    round(t_mean, 2),
                'TAKIM STD':     round(t_std, 2),
                'PERCENTILE':    round(pct, 1),
                'Z-SCORE':       round(z, 2),
                'SEVİYE':        AnalyticsEngine._level_label(pct).upper(),
                '_metric_key':   m,  # iç kullanım — filtre için
            })

        return pd.DataFrame(rows)

    # ── Yük Spike Tespiti ─────────────────────────────────────────────────────
    @staticmethod
    def detect_load_spikes(player_data: pd.DataFrame,
                            metric: str = 'player_load',
                            z_threshold: float = None) -> pd.DataFrame:
        """
        Belirli bir metrikte ani yük artışlarını tespit eder.
        Dönüş: spike olan satırları içeren DataFrame.
        """
        if z_threshold is None:
            z_threshold = THRESHOLDS['anomaly_z']

        df   = player_data.sort_values('tarih').copy()
        mask = AnalyticsEngine.detect_anomalies(df, metric, z_threshold)
        spikes = df[mask][['tarih', 'tip', metric]].copy()

        if not spikes.empty:
            spikes['tarih'] = pd.to_datetime(spikes['tarih']).dt.strftime('%d.%m.%Y')
            from config import METRICS as METRIC_DEF
            m_info = METRIC_DEF.get(metric, {'display': metric, 'unit': ''})
            spikes.columns = ['Tarih', 'Seans', f"{m_info['display'].upper()} ({m_info['unit']})"]

        return spikes

    # ── Yardımcı: Seviye Etiketi ──────────────────────────────────────────────
    @staticmethod
    def _level_label(pct: float) -> str:
        """Percentile değerinden Türkçe seviye etiketi üretir."""
        if pct >= THRESHOLDS['elite_percentile']:
            return '🟢 ELİT'
        if pct >= THRESHOLDS['good_percentile']:
            return '🔵 İYİ'
        if pct >= THRESHOLDS['avg_percentile']:
            return '🟡 ORTA'
        return '🔴 DÜŞÜK'

    # ── Özet İstatistik ───────────────────────────────────────────────────────
    @staticmethod
    def summary_stats(data: pd.DataFrame, metrics: list = None) -> pd.DataFrame:
        """
        Veri setinin metrik bazlı özet istatistikleri.
        Dönüş: DataFrame — Metrik | N | Min | Ort | Max | Std | Median
        """
        if metrics is None:
            metrics = PRIMARY_METRICS

        from config import METRICS as METRIC_DEF
        rows = []

        for m in metrics:
            if m not in data.columns:
                continue
            s = data[m].dropna()
            if s.empty:
                continue
            
            # Min=0 kirliliğini önlemek için 0'ları Nan yapıp Min hesaplıyoruz
            s_no_zero = s.replace(0, np.nan).dropna()
            min_val = s_no_zero.min() if not s_no_zero.empty else 0.0

            rows.append({
                'METRİK':  METRIC_DEF.get(m, {}).get('display', m).upper(),
                'BİRİM':   METRIC_DEF.get(m, {}).get('unit', ''),
                'N':       len(s),
                'MİN':     round(float(min_val), 2),
                'ORT.':    round(float(s.mean()), 2),
                'MEDYAN':  round(float(np.median(s.values)), 2),
                'MAX':     round(float(s.max()), 2),
                'STD':     round(float(s.std(ddof=1)), 2) if len(s) > 1 else 0.0,
            })

        return pd.DataFrame(rows)


# ─── Singleton ───────────────────────────────────────────────────────────────
analytics_engine = AnalyticsEngine()