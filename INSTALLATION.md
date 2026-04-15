# ⚙️ RUGBY SİSTEMİ v5.0 - KURULUM KILAVUZU

## 📋 İÇİNDEKİ DOSYALAR

### 🎯 ANA DOSYALAR (Kök Dizin)
```
app.py                    - Ana uygulama giriş noktası
config.py                 - Konfigürasyon ve ayarlar
styles.py                 - CSS ve tema sistemi (14KB)
database.py               - Veritabanı yönetimi ve SQL işlemler
utils.py                  - Analiz, clustering, grafik fonksiyonları (25KB)
export_tools.py           - PNG, HTML, Excel export işlevleri
components.py             - UI bileşenleri
requirements.txt          - Python paketleri listesi
README.md                 - Proje dokümantasyonu
.streamlit/config.toml    - Streamlit konfigürasyonu
```

### 📱 SAYFA DOSYALARI (pages/ dizini)
```
01_Home.py                - 🏠 Ana Sayfa (YAŞ GRUBU SEÇİMİ)
02_Kamp_Analizi.py       - ⚽ KAMP ANALİZİ (Günlük sıralamalar)
03_Oyuncu_Profili.py     - 🏃 OYUNCU PROFİLİ (Kümeleme + Benzer Oyuncular)
04_Karsilastirma.py      - ⚔️ KARŞILAŞTIRMA (Renklendirilmiş H2H)
05_Siralamalar.py        - 📊 SIRALAMALAR (Genel, Kamp, Günlük)
06_Scatter.py            - 🎯 SCATTER ANALİZİ (İki metrik dağılımı)
07_Oyuncu_Galerisi.py    - 👥 OYUNCU GALERİSİ (Fotoğraflı kadro)
08_Istatistikler.py      - 📈 İSTATİSTİKLER (Box-plot, Trend, Korelasyon)
09_Admin_Panel.py        - ⚙️ ADMIN PANEL (Silme, Görsel, Audit Log)
11_Impact_Analysis.py    - ⚡ IMPACT ANALİZİ (Objektif performans)
```

## 🚀 1. ADIM: KURULUM

### A. Python Kurulumu (Varsa atla)
```bash
# Python 3.9+ gerekir
python --version  # kontrol et
```

### B. Gereksiz Paketleri Yükle
```bash
# Proje klasörüne gir
cd tff_performans

# Virtual environment (önerilir)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Paketleri yükle
pip install -r requirements.txt
```

## 🎬 2. ADIM: UYGULAMAYI BAŞLAT

```bash
streamlit run app.py
```

Tarayıcı otomatik açılacak: `http://localhost:8501`

## 📊 3. ADIM: VERİ YÜKLE

### Excel Dosya Formatı
Aşağıdaki sütunları içermelidir:

```
| tarih      | player_name    | age_group | tip      | minutes | total_distance | metrage | smax_kmh | dist_25_plus | player_load | amp | hsr | acc_over_3 | dec_under_minus_3 | high_accel_count | quick_change_of_direction | camp_id |
|-----------|----------------|-----------|----------|---------|---|---|---|---|---|---|---|---|---|---|---|
| 2024-01-15 | Ahmet YILMAZ   | 91U       | TRAINING | 90      | 9500 | 42 | 28.5 | 2100 | 450 | 180 | 15 | 8 | 5 | 12 | 3 | 1 |
```

### Yükleme İşlemi
1. Yan menüde "📂 VERİ YÜKLE" tıkla
2. Excel dosyası seç
3. Yaş grubunu belirle (71U, 91U, U20, _)
4. "✅ VERİTABANıNA AKTAR" tıkla

## 🔑 ADMIN PANEL ERİŞİMİ

**Şifre:** `tff2024`

### Admin İşlevleri
- ✅ Oyuncu silme
- ✅ Kamp silme
- ✅ Yaş grubu silme
- ✅ Oyuncu fotoğraf & logo güncelleme
- ✅ Audit Log görüntüleme
- ✅ Sistem özeti ve istatistikleri

## 📈 SAYFALARIN AÇIKLAMASI

### 🏠 ANA SAYFA (01_Home.py)
- Yaş grubu özetleri
- Genel sistem istatistikleri
- En iyi 10 performans
- Hızlı menü

### 🏃 OYUNCU PROFİLİ (03_Oyuncu_Profili.py)
**ÖZELLİKLER:**
- Performans grafiği ve takım bandı
- Min/Ort/Max tablosu
- Atletik Performans Skoru (0-100%)
- Radar profili
- **🆕 KÜMELEME ANALİZİ**
  - K-Means algoritması ile benzer oyuncu bulma
  - Benzerlik skoru (0-100%)
  - Detaylı metrik karşılaştırması

### ⚔️ KARŞILAŞTIRMA (04_Karsilastirma.py)
**YENİLİK:**
- Renklendirilmiş fark gösterimi
- Yeşil: Oyuncu 1 daha iyi
- Kırmızı: Oyuncu 2 daha iyi
- Gri: Eşit
- Yüzde ve mutlak fark gösterimi

### ⚡ IMPACT ANALİZİ (11_Impact_Analysis.py)
**FORMÜL:**
```
Impact Score = (
  25% × Yüksek Hızlı Koşu +
  20% × Patlayıcı Aksiyon +
  20% × Oyuncu Yükü +
  15% × Toplam Mesafe +
  10% × Maksimum Hız +
  10% × Metabolik Güç
)
```

## 🎨 SİSTEM ÖZELLİKLERİ

### ✅ VERİ YÖNETIMI
- SQLite veritabanı (lokal)
- Otomatik backup (production'da düşünün)
- Audit trail (tüm işlemler log'lanır)

### ✅ VİZUAL TASARIM
- TFF renkleri (Kırmızı #E30A17)
- Siyah/Füme sidebar
- Responsive (mobil uyumlu)
- Türkçe karakter desteği

### ✅ ANALİZ ARAÇLARI
- Kümeleme (K-Means)
- Percentile hesaplama
- Z-Score normalizasyonu
- İstatistiksel analiz

### ✅ EXPORT İŞLEMLERİ
- PNG İndir (metadata dahil)
- HTML İndir (interaktif)
- Excel İndir
- CSV İndir

## ⚡ PERFORMANS İPUCLARI

1. **İlk Yükleme Yavaş**
   - Streamlit cachcing otomatik etkin
   - Tekrar çalıştırmak daha hızlı

2. **Timeout Sorunu**
   ```bash
   streamlit run app.py --client.maxMessageSize=5
   ```

3. **Kaleido Hatası**
   ```bash
   pip install --upgrade kaleido
   ```

4. **Veritabanı Sıfırlama**
   ```bash
   rm tff_performans.db
   # Yeniden başlat ve verileri yükle
   ```

## 🔐 ÜRETİM AYARLARI

### Zorunlu Değişiklikler
1. **Admin Şifresini Değiştir**
   - `config.py`'de `ADMIN_PASSWORD` değerini değiştir

2. **Debug Modunu Kapat**
   - `config.py`'de `DEBUG_MODE = False`

3. **HTTPS Etkinleştir**
   - `.streamlit/config.toml`'de gerekli ayarları yap

4. **Veritabanını Cloud'a Taşı**
   - PostgreSQL, MySQL vb. kullan

## 📊 METRLER SÖZLÜĞÜ

| Metrik | Açıklama | Birim |
|--------|----------|-------|
| total_distance | Koşulan toplam mesafe | m |
| smax_kmh | Kaydedilen en yüksek hız | km/h |
| dist_25_plus | 25 km/h üzeri koşu mesafesi | m |
| player_load | Mekanik yük | Load |
| metrage | Metabolik güç | W/kg |
| hsr | Yüksek hızlı koşu sayısı | sayı |
| amp | Metabolik toparlanma | J/kg |

## 🆘 YAYGINU HATALAR

**"VERİ BULUNAMADI"**
- Excel dosyasının formatını kontrol et
- Yaş grubu seçimini kontrol et

**"KALEIDO HATASI"**
```bash
pip install kaleido
```

**"ADMIN ŞİFRE HATASI"**
- Şifre: `tff2024`
- CapsLock kontrol et

## 📞 DESTEK

Rugby Performans Sistemi
- 🌐 www.tff.org.tr
- 📧 support@tff.org.tr

---

**Kurulum Tamamlandı! 🎉**

Sorun yaşarsa README.md dosyasını kontrol edin.
