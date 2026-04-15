# Hesaplama Metodolojileri

## 1. Percentile Rank

### Tanım
Oyuncunun takım içindeki yüzdelik sıralaması.

### Formül
```
Percentile = (Oyuncudan Düşük Kişi Sayısı / Toplam) × 100
```

### Örnek
```
Takım: 20 oyuncu
Mesafe Sıralaması:
1. Ahmet - 5900m
2. Mehmet - 5800m
...
16. Fatih - 4800m (oyuncu)
...
20. Ali - 3900m

Fatih'in percentile:
- 15 oyuncu daha az koştu
- (15/20) × 100 = %75
```

### Yorumlama
- %80+ = Çok iyi (🟢 Yeşil)
- %65-79 = İyi (🔵 Mavi)
- %50-64 = Orta (🟠 Turuncu)
- %0-49 = Düşük (🔴 Kırmızı)

## 2. Z-Score

### Tanım
Ortalamadan kaç standart sapma uzakta olduğu.

### Formül
```
Z = (Değer - Ortalama) / Standart Sapma
```

### Örnek
```
Takım Mesafe:
- Ortalama: 5200m
- Std Dev: 400m
- Ahmet: 5900m

Z = (5900 - 5200) / 400 = 1.75
```

### Yorumlama
- Z > 2 = Çok yüksek
- 1 < Z < 2 = Yüksek
- -1 < Z < 1 = Normal
- Z < -2 = Çok düşük

## 3. Bileşik Skor

### Tanım
Tüm metriklerin ağırlıklı percentile ortalaması.

### Metrikleri
```
- Total Distance (ağırlık: 2.0)
- Metrage (ağırlık: 1.5)
- Dist 25+ (ağırlık: 1.5)
- SMax (ağırlık: 1.0)
- Player Load (ağırlık: 1.0)
- Dist 20-25 (ağırlık: 1.0)
- AMP (ağırlık: 0.5)
```

### Formül
```
Bileşik = Σ(Percentile × Ağırlık) / Σ(Ağırlık)
```

### Örnek
```
Ahmet percentile'leri:
- Total Distance: %85
- Metrage: %80
- Dist 25+: %78
- SMax: %75
- Player Load: %82
- Dist 20-25: %70
- AMP: %65

Bileşik = (85×2 + 80×1.5 + 78×1.5 + 75 + 82 + 70 + 65×0.5) / (2+1.5+1.5+1+1+1+0.5)
        = (170 + 120 + 117 + 75 + 82 + 70 + 32.5) / 8
        = 666.5 / 8
        = 83.3%
```

## 4. Anomali Tespiti

### Metodoloji
Z-Score > 2.5 olan değerler anomali olarak işaretlenir.

### Uyarı Türleri
- 🔴 **Çok Yüksek**: Z > 2.5
- 🟡 **Çok Düşük**: Z < -2.5
- 🟠 **Ani Değişim**: %30+ artış/azalış
- 🟢 **Sıfır Değer**: 0 olması beklenenmiyor

## 5. Trend Analizi

### Metodoloji
Linear regression (y = mx + b)

### Parametreler
- m = eğim (pozitif = artış, negatif = düşüş)
- Pearson r = korelasyon kuvveti

### Yorumlama
```
m > 0.05: 📈 Güçlü artış
0 < m < 0.05: 📈 Hafif artış
m = 0: ➡️ Sabit
-0.05 < m < 0: 📉 Hafif düşüş
m < -0.05: 📉 Güçlü düşüş
```

## 6. Heatmap Renklendirmesi

### Renkler
- Kırmızı: Düşük performans
- Sarı: Orta performans
- Yeşil: Yüksek performans

### Hesaplama
```
Renk = (Değer - Min) / (Max - Min)
```

## Önemli Notlar

1. **Eksik Veriler**: NaN değerler hesaplara dahil edilmez
2. **Bölüm Süresi**: Dakika < 30 ise sonuç %80 normalize
3. **Takım Ortalaması**: Sadece aynı seans tipinde hesaplanır
4. **Percentile Caching**: Performans için cache'leme yapılır
