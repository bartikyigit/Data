# 🎨 FAZ 2 - GÖRSEL SİSTEM KILAVUZU

## 📊 KART RENDER FONKSİYONLARI

### 1. Oyuncu Performans Kartı

Seçili kamptaki oyuncunun genel performansını gösteren kart.

```python
from utils import render_performance_card

stats = {
    'session_count': 5,
    'avg_distance_camp': 8500,
    'max_speed_camp': 32.5,
    'avg_load_camp': 92.3
}

render_performance_card(
    player_name='Ali Yılmaz',
    icon='⚽',
    stats=stats,
    camp_name='U17 Kamp - Şubat 2026',
    score=75.0  # Bileşik skor
)
```

**Gösterilenler:**
- Oyuncu adı + ikon
- Kamp adı
- Toplam seans sayısı
- Ortalama mesafe
- Maksimum hız
- Ortalama yük
- Bileşik skor (renki: percentile'ye göre)

---

### 2. Min/Ort/Max Kartı (Durum Göstergeli)

Her metrik için minimum, ortalama, maksimum değerleri + oyuncu performansını gösteren kart.

```python
from utils import render_minmax_card, calculate_rank_position

# Takım verilerinden sıralama hesapla
rank_pos = calculate_rank_position(player_distance, team_distances)

render_minmax_card(
    metric_name='Toplam Mesafe',
    player_value=8500.0,
    team_min=7200.0,
    team_avg=8100.0,
    team_max=9800.0,
    rank_pos=rank_pos,  # (6, 20) örneği
    percentile=75.0,
    unit='m'
)
```

**Özellikleri:**
- Renkli border (percentile'ye göre: elite/good/medium/low)
- Oyuncu değeri kırmızı highlight
- Takım sırası badge (6/20 formatı)
- Percentile göstergesi (%75)
- Min/Ort/Max değerleri grid'de

---

## 🏷️ BADGE RENDER FONKSİYONLARI

### 1. Performans Seviyesi Badge

```python
from utils import render_status_badge

html_badge = render_status_badge(75.0)
# Çıktı: <span class="badge-status badge-good">✨ İYİ</span>

st.markdown(html_badge, unsafe_allow_html=True)
```

**Seviyeler:**
- 80%+: 🌟 ELİT (yeşil)
- 65-79%: ✨ İYİ (mavi)
- 50-64%: → ORTA (sarı)
- <50%: ⚠️ DÜŞÜK (kırmızı)

---

### 2. Gelişim Yönü Badge

```python
from utils import render_growth_badge

html_badge = render_growth_badge(+8.5)  # +8,5% gelişim
# Çıktı: <span class="badge-status badge-good">▲ +8,50% (İyi)</span>

st.markdown(html_badge, unsafe_allow_html=True)
```

**Seviyeleri:**
- +10%+: ▲ Mükemmel (koyu yeşil)
- +5% ile +10%: ▲ İyi (açık yeşil)
- -5% ile +5%: → Stabil (sarı - RİSKLİ)
- -5% ile -10%: ▼ Düşüş (turuncu)
- -10%-: ▼ Kritik (kırmızı)

---

### 3. Seans Tipi Badge

```python
from utils import render_session_type_badge

badge_maç = render_session_type_badge('MATCH')
badge_ant = render_session_type_badge('TRAINING')

st.markdown(badge_maç + " " + badge_ant, unsafe_allow_html=True)
```

---

### 4. Impact Score Badge

```python
from utils import render_impact_level_badge

badge = render_impact_level_badge(82.5)
# Çıktı: <span class="badge-status badge-elite">⭐ IMPACT: 82</span>

st.markdown(badge, unsafe_allow_html=True)
```

---

## 💬 TOOLTIP FONKSIYONLARI

### 1. Detaylı Tooltip Kutusu (Bilgi Göster)

Oyuncu performansıyla ilgili tüm detayları bir kutu içinde göster.

```python
from utils import render_tooltip_box

render_tooltip_box(
    player_name='Ali Yılmaz',
    metric='total_distance',
    raw_value=8500.0,
    normalized_value=94.4,
    team_rank=(6, 20),
    percentile=75.0,
    team_avg=8100.0,
    show_box=True
)
```

**İçeriği:**
- Oyuncu adı (başlık)
- Metrik türü (Toplam Mesafe)
- Ham değer (8.500,0 m) - KIRMIZI
- Takım sırası (6/20)
- Yüzdelik dilim (75%) - RENKLİ
- Takım ortalaması (8.100,0 m)
- Durum etiketi (✨ İYİ PERFORMANS)

**Görünüm:**
```
┌─────────────────────────┐
│ ALİ YILMAZ              │
├─────────────────────────┤
│ Metrik: Toplam Mesafe   │
│ Ham Değer: 8.500,0 m    │
│ Takım Sırası: 6/20      │
│ Yüzdelik: 75%           │
│ Takım Ort.: 8.100,0 m   │
├─────────────────────────┤
│ ✨ İYİ PERFORMANS       │
└─────────────────────────┘
```

---

### 2. Metrik Açıklama Kartı

Metrik nedir, nasıl hesaplanır, ne anlama gelir sorusuna cevap veren kart.

```python
from utils import render_metric_explanation

render_metric_explanation(
    metric='total_distance',
    calculation='Tüm hareketi metre cinsinden toplamı',
    interpretation='Yüksek değer = daha fazla hareket',
    color_meaning='Yeşil = Elite, Kırmızı = Düşük'
)
```

---

### 3. Info Tooltip (Başlık Yanında)

```python
from utils import render_info_tooltip

html = render_info_tooltip(
    "Min/Ort/Max Analizi",
    "Oyuncunun minimum, ortalama ve maksimum performans değerlerini gösterir"
)

st.markdown(html, unsafe_allow_html=True)
```

**Görünüm:** Min/Ort/Max Analizi ℹ️ (hover'da tooltip)

---

## 🎯 HIZLI YÖNETİCİ FONKSIYONLARI

### Durum Metni & Renk Alma

```python
from utils import get_performance_status_text, get_rank_color

# Durum metni
metin, renk = get_performance_status_text(75.0)
# Çıktı: ("✨ İYİ PERFORMANS", "#2563EB")

# Sıralama rengi
rank_color = get_rank_color(6, 20)
# Çıktı: Kırmızı ← Yeşil gradient
```

---

## 📋 SAYFA ENTEGRASYONU ÖRNEĞİ

```python
import streamlit as st
from utils import (
    render_performance_card, render_minmax_card,
    render_status_badge, render_tooltip_box,
    calculate_rank_position
)

# Page başlığı
st.title("🏃 Oyuncu Profili")

# 1. Performans Kartı
render_performance_card(
    player_name='Ali Yılmaz',
    icon='⚽',
    stats=stats,
    camp_name='U17 Kamp',
    score=75.0
)

st.divider()

# 2. Min/Ort/Max Kartları (6 metrik için)
for metric in ['total_distance', 'metrage', 'smax_kmh', ...]:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        render_minmax_card(
            metric_name=METRICS[metric]['display'],
            player_value=player_data[metric].mean(),
            team_min=team_data[metric].min(),
            team_avg=team_data[metric].mean(),
            team_max=team_data[metric].max(),
            rank_pos=calculate_rank_position(...),
            percentile=calculate_percentile_rank(...),
            unit=METRICS[metric]['unit']
        )
    
    with col2:
        st.markdown(render_status_badge(percentile), unsafe_allow_html=True)

st.divider()

# 3. Detaylı Tooltip (Modal benzeri)
with st.expander("📊 Detaylı Metrik Analizi"):
    render_tooltip_box(
        player_name='Ali Yılmaz',
        metric='total_distance',
        raw_value=8500.0,
        normalized_value=94.4,
        team_rank=(6, 20),
        percentile=75.0,
        team_avg=8100.0
    )
```

---

## 🎨 CSS KLASLARı (Doğrudan Kullanabilirsin)

Eğer kendi HTML'ini yazıyorsan:

```html
<!-- Performans Kartı -->
<div class="perf-card">
    <div class="perf-stat">
        <div class="perf-stat-val">8500</div>
        <div class="perf-stat-lbl">MESAFE (M)</div>
    </div>
</div>

<!-- Min/Max Kartı -->
<div class="minmax-card elite">
    <div class="minmax-metric">Toplam Mesafe</div>
    <div class="minmax-values">
        <div class="minmax-value">...</div>
    </div>
</div>

<!-- Badge'ler -->
<span class="badge-status badge-elite">🌟 ELİT</span>
<span class="badge-status badge-good">✨ İYİ</span>

<!-- Score Göstergesi -->
<div class="score-display">
    <div class="score-number">75</div>
    <div class="score-label">BİLEŞİK SKOR</div>
</div>
```

---

## ⚙️ İLERİ KULLANIM

### Dinamik Renk Belirleme

```python
from utils import percentile_color, COLORS

# Oyuncuya göre renk
color = percentile_color(75.0)  # "rgb(101, 150, 96)"

# Kullanım
st.markdown(f"<div style='color: {color};'>Yüzdelik: 75%</div>", unsafe_allow_html=True)
```

### Plotly Hover Template'i

```python
from utils import create_hover_template

for player in players:
    hover_text = create_hover_template(
        player_name='Ali',
        metric='total_distance',
        value=8500,
        rank=(6, 20),
        pct=75.0,
        team_avg=8100.0
    )
    # Grafiklerde hover olarak kullan
    fig.add_trace(..., hovertemplate=hover_text)
```

---

## 📝 NOTLAR

- **Renk Sistemi:** Tüm renkler `config.py`'daki `COLORS` dict'ten gelir
- **Türkçe Formatı:** `format_number()`, `format_percent()`, `format_rank()` kullan
- **Responsive:** CSS grid'leri responsive tasarlanmış
- **Erişilebilirlik:** WCAG AA standartlarına uygun kontrastlar

---

**Sorular?** Komment bırak! 🚀
