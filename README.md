<<<<<<< HEAD
# 🇹🇷 RUGBY SİSTEMİ v5.0
=======
# PERFORMANS SİSTEMİ v5.0
>>>>>>> 03d2fda26430649caa7ae6561991e2960b6e6d7c

Rugby Performans Sistemi Genç Takımları için profesyonel atletik veri analiz platformu.

## ✨ YENİLİKLER (v5.0)

### 🎨 GÖRÜNÜM & TASARIM
- ✅ ** Logosu Entegrasyonu** - Sayfanın en üstünde TFF logosu
- ✅ **Siyah/Füme Sidebar** - Modern, göz yormayan tasarım
- ✅ **Profesyonel Kartlar** - Tüm sayılarda kutulara alınmış metrikler
- ✅ **Mobil Optimizasyon** - Responsive design her cihaz için
- ✅ **Türkçe Karakter Desteği** - Tüm başlıklar ve metinler tamamen Türkçe

### 📊 YENİ ÖZELLİKLER
- ✅ **Atletik Performans Skoru** - Bileşik skor (Composite Score) yeniden adlandırıldı
- ✅ **Kümeleme Analizi** - K-Means algoritması ile benzer oyuncuları otomatik bulma
- ✅ **Benzer Oyuncular Sistemi** - Percentile-tabanlı benzerlik hesaplaması (0-100%)
- ✅ **Admin Silme İşlevleri** - Excel, Kamp, Oyuncu ve Yaş Grubu silme
- ✅ **Maç Günü Bayrak Logosu** - Kamp programında ülke bayrakları
- ✅ **Ana Sayfa İstatistikleri** - En çok kamplar, antrenmalar, maçlar listesi

### 📈 IYILEŞTIRMELER
- ✅ **Grafik Tabletleri** - Sütun ve Radar grafikleri tek tuşla değiştirme
- ✅ **Renklendirilmiş Karşılaştırma** - Fark gösterimi renk-koduyla (Yeşil/Kırmızı)
- ✅ **Impact Score Engine** - Z-Skoru tabanlı objektif performans metriği
- ✅ **Açıklamalar Sistemi** - Her grafik ve metrikteki tooltip bilgileri
- ✅ **PNG İndirmede Metadata** - Oyuncu adı, kamp, yaş grubu, tarih gibi detaylar
- ✅ **Streamlit Timeout Çözümü** - Session state optimizasyonu

## 📁 PROJE YAPISI

```
tff_performans/
├── app.py                          # Ana uygulama
├── config.py                       # Konfigürasyon
├── styles.py                       # Stil sistemi
├── database.py                     # Veritabanı yönetimi
├── utils.py                        # Analiz & grafikler
├── export_tools.py                 # İndirme işlevleri
├── components.py                   # UI bileşenleri
├── requirements.txt                # Python paketleri
├── tff_performans.db              # SQLite Veritabanı
├── .streamlit/
│   └── config.toml                # Streamlit ayarları
└── pages/
    ├── 01_Home.py                 # Ana Sayfa
    ├── 02_Kamp_Analizi.py         # Kamp Analizi
    ├── 03_Oyuncu_Profili.py       # Oyuncu Profili (Kümeleme)
    ├── 04_Karsilastirma.py        # Karşılaştırma
    ├── 05_Siralamalar.py          # Sıralamalar
    ├── 06_Scatter.py              # Scatter Analizi
    ├── 07_Oyuncu_Galerisi.py      # Oyuncu Galerisi
    ├── 08_Istatistikler.py        # İstatistikler & Trendler
    ├── 09_Admin_Panel.py          # Admin Panel (Silme, Görsel)
    └── 11_Impact_Analysis.py      # Impact Analizi
```

## 🚀 KURULUM

### Gereksinimler
- Python 3.9+
- pip paket yöneticisi

### Adım 1: Depoyu İndir
```bash
git clone <repo-url>
cd tff_performans
```

### Adım 2: Paketleri Yükle
```bash
pip install -r requirements.txt
```

### Adım 3: Uygulamayı Çalıştır
```bash
streamlit run app.py
```

Tarayıcıda otomatik olarak `http://localhost:8501` açılacak.

## 📊 KULLANIM

### 1. VERİ YÜKLEME
- Yan menüden Excel dosyası seçin
- Yaş grubunu belirtin (U17, U19, U20, _)
- "VERİTABANıNA AKTAR" butonu ile yükleyin

### 2. OYUNCU ANALİZİ
- **Oyuncu Profili** sekmesinden oyuncu seçin
- Atletik Performans Skorunu (percentile) görün
- **Benzer Oyuncular** sekmesinde kümeleme analizi yapın
- **Min/Ort/Max** tablosu ile detay analiz

### 3. KARŞILAŞTIRMALAR
- İki oyuncu seçerek H2H karşılaştırma yapın
- Renklendirilmiş fark gösterimi ile net farklı görin
- Gün ve Kamp bazında karşılaştırma seçeneği

### 4. YÖNETİM (ADMIN)
- Şifre: `tff2024`
- Oyuncu silme
- Kamp silme
- Yaş grubu silme
- Oyuncu fotoğraf & logo güncelleme
- Audit log görüntüleme

## 🎯 KÜLİM ANALİZİ AÇIKLAMASI

### Atletik Performans Skoru (Percentile)
- **%80+**: 🟢 Mükemmel - Takımın en iyi %20'si
- **%65-80**: 🔵 İyi - Takımın üstü
- **%50-65**: 🟡 Orta - Takım ortalaması yakını
- **<50**: 🔴 Düşük - Geliştirme gereken alan

### Impact Score (Etki Skoru)
Tüm atletik metriklerin Z-Skoru ile hesaplanmış objektif puanı:
- **%25** Yüksek Hızlı Koşu (25+ km/h)
- **%20** Patlayıcı Aksiyon (İvmelenme + Yavaşlama)
- **%20** Oyuncu Yükü (Mekanik Yük)
- **%15** Toplam Mesafe (Hacim)
- **%10** Maksimum Hız
- **%10** Metabolik Güç

### Kümeleme Analizi
K-Means algoritması kullanarak benzer oyuncuları otomatik olarak gruplandırır:
- Tüm 11 metrik temel alır
- Benzerlik Skoru 0-100% arasında gösterilir
- Aynı kümede yer alan oyuncuların özellikleri benzerdir

## 📥 EXCEL İÇİN GEREKLI SÜTUNLAR

```
tarih | player_name | tip | minutes | total_distance | smax_kmh | 
player_load | metrage | dist_25_plus | hsr | amp | 
acc_over_3 | dec_under_minus_3 | high_accel_count | quick_change_of_direction | camp_id
```

**Örnek Format:**
```
2024-01-15 | Ahmet YILMAZ | MATCH | 90 | 9500 | 32.5 | 450 | ...
```

## 🔐 GÜVENLIK

- Admin Panel şifresi: `tff2024` (production'da değiştirin!)
- Tüm işlemler audit log'a kaydedilir
- SQLite lokal veritabanı (cloud backup'ı düşünün)

## 📱 MOBİL UYUMLULUK

- **Responsive Design**: Tüm cihazlara uyar
- **Touch-Friendly Buttons**: Mobil dokunuşlar için optimize
- **Compact Layout**: Dar ekranlar için sıkıştırılmış görünüm

## 🆘 SORUN GİDERME

### Streamlit Timeout
```bash
streamlit run app.py --client.maxMessageSize=5
```

### Kaleido Hatası (PNG Export)
```bash
pip install --upgrade kaleido
```

### Veritabanı Sıfırlama
```bash
rm tff_performans.db
# Uygulamayı yeniden çalıştırın
```

## 📞 İLETİŞİM

Rugby Performans Sistemi
- 🌐 www.tff.org.tr
- 📧 info@tff.org.tr

---

**Versiyon:** 5.0
**Son Güncelleme:** Şubat 2026
**Geliştirici:** TFF Teknoloji & Analiz Departmanı
