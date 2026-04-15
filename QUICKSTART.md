# 🚀 QUICK START GUIDE - Visual Studio Code

## 1️⃣ PRoje Dizini Oluştur

```bash
mkdir tff_performance_system
cd tff_performance_system
```

## 2️⃣ Dosya Yapısını Oluştur

```bash
# Windows (PowerShell)
mkdir pages
mkdir .streamlit

# macOS/Linux (Bash)
mkdir -p pages .streamlit
```

## 3️⃣ Kopyala/Yapıştır Sırası

Aşağıdaki dosyaları sırasıyla oluştur ve içeriklerini kopyala:

### 🔴 ROOT LEVEL (Proje Kökü)

1. **config.py** - ✅ Kopyala
   - Renkler ve sabitler

2. **database.py** - ✅ Kopyala
   - Veritabanı yönetimi

3. **utils.py** - ✅ Kopyala
   - Görselleştirme fonksiyonları

4. **app.py** - ✅ Kopyala
   - ANA STREAMLIT DOSYASI (bu app.py adında olmalı!)

5. **requirements.txt** - ✅ Kopyala
   - Bağımlılıklar

6. **README.md** - ✅ Kopyala
   - Rehber

### 🟦 Pages Klasörü (pages/)

1. **pages/01_🏠_Home.py** - ✅ Kopyala
   - Ana sayfa

2. **pages/02_⚽_Kamp_Analizi.py** - ✅ Kopyala
   - Kamp analizi

3. **pages/03_🏃_Oyuncu_Profili.py** - ✅ Kopyala
   - Oyuncu profili

4. **pages/04_⚔️_Karşılaştırma.py** - ✅ Kopyala
   - Oyuncu karşılaştırması

5. **pages/05_📊_Sıralamalar.py** - ✅ Kopyala
   - Sıralamalar

### ⚙️ Streamlit Config (.streamlit/)

1. **.streamlit/config.toml** - ✅ Kopyala
   - Streamlit ayarları

## 4️⃣ Sanal Ortam Kur

```bash
# Sanal ortam oluştur
python -m venv venv

# Aktivasyon
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

## 5️⃣ Bağımlılıkları Yükle

```bash
pip install -r requirements.txt
```

## 6️⃣ Uygulamayı Çalıştır

```bash
streamlit run app.py
```

✅ Tarayıcında otomatik açılacak: http://localhost:8501

## 7️⃣ Excel Dosyaları Yükle

1. Sidebar'da "📂 Veri Yönetimi" bölümünde
2. Excel dosyasını yükle (91U_ŞUBAT.xlsx, 71U_EYLÜL.xlsx vb.)
3. Yaş grubunu seç
4. "✅ Veritabanına Aktar" butonuna tıkla

---

## 📁 Son Proje Yapısı

```
tff_performance_system/
├── config.py                    ✅
├── database.py                  ✅
├── utils.py                     ✅
├── app.py                       ✅ (ANA DOSYA)
├── requirements.txt             ✅
├── README.md                    ✅
├── .streamlit/
│   └── config.toml             ✅
├── pages/
│   ├── 01_🏠_Home.py           ✅
│   ├── 02_⚽_Kamp_Analizi.py   ✅
│   ├── 03_🏃_Oyuncu_Profili.py ✅
│   ├── 04_⚔️_Karşılaştırma.py  ✅
│   └── 05_📊_Sıralamalar.py    ✅
└── venv/                        (sanal ortam - gitignore)
```

## ⚡ İlk Çalıştırmada

- Veritabanı otomatik oluşturulur: `tff_performans.db`
- Hiçbir manuel SQL kodu gerekmez
- Tüm ayarlar otomatiktir

## 🎯 Örnek Kullanım

### Veri Yükle
1. Excel dosyasını sidebar'dan yükle
2. 91U / 71U / 61U / _ seç
3. "Veritabanına Aktar" tıkla

### Ana Sayfada
- Yaş gruplarını görebilir
- Her yaş grubu kartına tıkla

### Kamp Analizi
- Yaş grubu → Kamp → Tarih seç
- Günlük sıralamalarını görebilir

### Oyuncu Profili
- Oyuncu seç → Kamp seç
- Performans grafiklerini görebilir
- Radar analiz ile takımla kıyasla

### Karşılaştırma
- 2 oyuncu seç veya çoklu radar
- Sütun grafikleri görebilir

### Sıralamalar
- Günlük, kamp veya bileşik sıralama
- Metrik seçerek sıralanabilir

---

## 🔧 Eğer Hata Alırsan

### "ModuleNotFoundError: No module named 'streamlit'"
```bash
pip install -r requirements.txt
```

### "No such table: performance_data"
- `tff_performans.db` dosyasını sil
- Uygulamayı yeniden başlat

### "Turkish characters not showing"
- Dosya kodlamasını UTF-8 yapın (VS Code'da sağ alt)

### Türkçe karakter hatası
- İşletim sisteminizin UTF-8 desteğini kontrol edin

---

## 📚 VS Code Tıpları

### Debug Modu
```bash
streamlit run app.py --logger.level=debug
```

### Port Değiştir
```bash
streamlit run app.py --server.port 8502
```

### Browser'ı Otomatik Açma
```bash
streamlit run app.py --client.showErrorDetails=true
```

---

**Hepsi Hazır! Başlamaya Hazırsın! 🚀⚽🇹🇷**
