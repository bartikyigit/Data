# Değişken Haritası

## Excel'den Veritabanına Eşleme

| Excel Sütunu | DB Adı | Açıklama |
|---|---|---|
| Name | player_name | Oyuncu adı |
| Tarih | tarih | Seans tarihi (DD.MM.YYYY) |
| Minutes | minutes | Oynama süresi (dakika) |
| Total Distance | total_distance | Toplam koşu mesafesi (metre) |
| Metrage | metrage | Yüksek intensiteli mesafe (metre) |
| Dist 20-25 | dist_20_25 | 20-25 km/h mesafe (metre) |
| Dist > 25 | dist_25_plus | >25 km/h mesafe (metre) |
| Dist Acc>3 | dist_acc_3 | >3 m/s² hızlanma (metre) |
| Dist Dec<-3 | dist_dec_3 | <-3 m/s² yavaşlama (metre) |
| SMax (kmh) | smax_kmh | Maksimum hız (km/h) |
| Player Load | player_load | Cumulative playload |
| AMP | amp | Absolute metabolic power |
| N 20-25 | n_20_25 | 20-25 km/h koşu sayısı |
| N > 25 | n_25_plus | >25 km/h koşu sayısı |
| Tip | tip | TRAINING veya MATCH |

## Gerekli vs Opsiyonel

### Gerekli (Hepsi var olmalı)
- Name, Tarih, Minutes, Total Distance, Metrage
- Dist 20-25, Dist > 25, SMax, Player Load, AMP, Tip

### Opsiyonel (Yoksa atlanır)
- Dist Acc>3, Dist Dec<-3
- N 20-25, N > 25

## Veri Formatları

### Tarih
- **Kabul**: 01.02.2026, 1.2.2026
- **RED**: 2026-01-02, 01/02/2026

### Sayılar
- **Kabul**: 1000, 1000.5, "1000,5"
- **RED**: "1000m", "1000 m"

### Seans Tipi
- **Kabul**: TRAINING, Training, training, MATCH, Match, match
- **RED**: Antrenman, Maç
