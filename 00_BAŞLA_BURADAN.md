# 🇹🇷 RUGBY TAKIP SISTEMI - KURULUM REHBERI

## ⭐ BUNU İLK OKU!

Bu klasörde bulduğun dosyalar, profesyonel bir Streamlit uygulamasını oluşturmak için gerekli olan tüm kodlardır.

---

## 📋 ADIM ADIM KURULUM

### **ADIM 1: Proje Klasörü Oluştur**

Visual Studio Code'da veya terminal'de:

```bash
mkdir tff_performance_system
cd tff_performance_system
```

### **ADIM 2: Root Level Dosyaları Kopyala**

Aşağıdaki dosyaları proje klasörüne kopyala:

```
tff_performance_system/
├── 01_config.py              👈 BURADAN KOPYALa → config.py
├── 02_database.py            👈 BURADAN KOPYALa → database.py
├── 03_utils.py               👈 BURADAN KOPYALa → utils.py
├── 04_app.py                 👈 BURADAN KOPYALa → app.py (ÖNEMLİ!)
├── requirements.txt          👈 BURADAN KOPYALa (AYNEN)
└── README.md                 👈 BURADAN KOPYALa (AYNEN)
```

**Kopyalama Şekli:**
1. `01_config.py` açılır
2. Tüm içeriği seç (Ctrl+A)
3. Kopyala (Ctrl+C)
4. VS Code'da yeni dosya oluştur: `config.py`
5. Yapıştır (Ctrl+V)
6. Kaydet (Ctrl+S)

**ÖNEMLİ:** `04_app.py` dosyasını **`app.py`** adıyla kaydet!

### **ADIM 3: pages/ Klasörü Oluştur**

```bash
mkdir pages
```

Aşağıdaki dosyaları pages klasörüne kopyala:

```
pages/
├── 07_01_Home.py             👈 BURADAN KOPYALa → 01_🏠_Home.py
├── 08_02_Kamp_Analizi.py     👈 BURADAN KOPYALa → 02_⚽_Kamp_Analizi.py
├── 09_03_Oyuncu_Profili.py   👈 BURADAN KOPYALa → 03_🏃_Oyuncu_Profili.py
├── 10_04_Karşılaştırma.py    👈 BURADAN KOPYALa → 04_⚔️_Karşılaştırma.py
└── 11_05_Sıralamalar.py      👈 BURADAN KOPYALa → 05_📊_Sıralamalar.py
```

**Dosya Adları ÖNEMLİ!** Emoji karakterleri kullan. Streamlit multi-page yapısı bu adlara göre çalışır.

### **ADIM 4: .streamlit/ Klasörü Oluştur**

```bash
mkdir .streamlit
```

`06_config.toml` dosyasını `.streamlit/` klasörüne kopyala:

```
.streamlit/
└── 06_config.toml            👈 BURADAN KOPYALa → config.toml
```

### **ADIM 5: Sanal Ortam Kur**

```bash
# Sanal ortam oluştur
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

### **ADIM 6: Bağımlılıkları Yükle**

```bash
pip install -r requirements.txt
```

Bu adım 2-3 dakika sürebilir.

### **ADIM 7: Uygulamayı Çalıştır**

```bash
streamlit run app.py
```

✅ Tarayıcında otomatik açılacak: http://localhost:8501

---

## 🎉 BAŞARILI KURULUM!

E�er uygulamayı gördüysen, tebrikler! Şimdi veri yüklemeye başlayabilirsin.

### Veri Yükleme:

1. **Sol Sidebar'da** → "📂 Veri Yönetimi" bölümü
2. **Excel dosyası seç** (U19_ŞUBAT.xlsx gibi)
3. **Yaş grubu seç** (U16, U17, U19, _)
4. **"✅ Veritabanına Aktar" butonuna tıkla**

---

## 📊 Hızlı Test

1. **Ana Sayfa** (🏠) - Yaş gruplarını görebilir
2. **Kamp Analizi** (⚽) - Kampları görebilir
3. **Oyuncu Profili** (🏃) - Oyuncu seçip grafikler görebilir
4. **Karşılaştırma** (⚔️) - Oyuncu karşılaştırması
5. **Sıralamalar** (📊) - Günlük/kamp sıralamalarını görebilir

---

## 📁 Son Proje Yapısı

```
tff_performance_system/
├── config.py                  ✅
├── database.py                ✅
├── utils.py                   ✅
├── app.py                     ✅ (ANA DOSYA - ÖNEMLİ!)
├── requirements.txt           ✅
├── README.md                  ✅
├── tff_performans.db          (otomatik oluşturulur)
├── venv/                      (sanal ortam)
├── .streamlit/
│   └── config.toml           ✅
└── pages/
    ├── 01_🏠_Home.py         ✅
    ├── 02_⚽_Kamp_Analizi.py ✅
    ├── 03_🏃_Oyuncu_Profili.py ✅
    ├── 04_⚔️_Karşılaştırma.py ✅
    └── 05_📊_Sıralamalar.py  ✅
```

---

## ⚠️ Sık Karşılaşılan Sorunlar

### "ModuleNotFoundError: No module named 'streamlit'"
- Sanal ortamı aktif ettin mi? (venv\Scripts\activate)
- `pip install -r requirements.txt` çalıştır

### "Turkish characters not showing"
- VS Code'da sağ alt → Kodlamayı UTF-8 yap

### Grafikleri göremiyorum
- Tarayıcı cache'ini temizle (Ctrl+Shift+Delete)
- Sayfayı yenile (F5)

### "No such table: performance_data"
- `tff_performans.db` dosyasını sil
- Uygulamayı yeniden başlat

### pages/02_⚽_Kamp_Analizi.py hatası
- Dosya adında emoji kullan
- Streamlit multi-page yapısı buna bağlı çalışır

---

## 🎯 Ne Yapabileceğin

✅ Yaş gruplarına göre verileri organize et
✅ Kamp analizi yap (günlük sıralamalar)
✅ Oyuncu profillerini görüntüle
✅ Oyuncuları karşılaştır
✅ Sıralamalar yap (günlük, kamp, bileşik)
✅ Training/Match ayrımıyla grafikler gör
✅ Takım ortalaması bandı ile perform analiz
✅ Radar grafiklerle multidimensiyonel karşılaştırma

---

## 📚 Daha Fazla Bilgi

- **README.md** - Detaylı rehber
- **QUICKSTART.md** - Hızlı başlangıç
- **config.py** - Renk şeması ve ayarlar

---

## 🆘 Yardım İhtiyacın Varsa

1. **README.md** dosyasını oku
2. **QUICKSTART.md** dosyasını kontrol et
3. **Hata mesajını oku** - Çoğu zaman çözüm orada

---

**Başarılar! 🇹🇷⚽🚀**

Rugby Performans Sistemi v1.0.0
