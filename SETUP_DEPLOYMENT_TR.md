# 🚀 Rugby Performans Sistemi - Kurulum & Deployment Rehberi

**Version:** 5.0 (Optimized)  
**Last Updated:** Şubat 2026

---

## 📋 İçindekiler

1. [Hızlı Başlangıç](#-hızlı-başlangıç)
2. [Sistem Gereksinimleri](#-sistem-gereksinimleri)
3. [Yerel Kurulum](#-yerel-kurulum)
4. [Dosya Yapısı](#-dosya-yapısı)
5. [Konfigürasyon](#-konfigürasyon)
6. [Streamlit Deployment](#-streamlit-deployment)
7. [Üretim Ortamı Ayarları](#-üretim-ortamı-ayarları)

---

## 🎯 Hızlı Başlangıç

### 1. Depoyu Clone Et
```bash
git clone <repository-url>
cd tff_performans_sistemi
```

### 2. Virtual Environment Oluştur
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Bağımlılıkları Yükle
```bash
pip install -r requirements.txt
```

### 4. Uygulamayı Çalıştır
```bash
streamlit run app.py
```

**Beklenen Çıktı:**
```
Local URL: http://localhost:8501
Network URL: http://<your-ip>:8501
```

---

## 💻 Sistem Gereksinimleri

### Minimum Gereksinimler
- **Python:** 3.9+
- **RAM:** 4GB (2GB minimum)
- **Storage:** 500MB
- **İnternet:** İlk yükleme için gerekli

### Önerilen Spec
- **Python:** 3.10+
- **RAM:** 8GB+
- **Storage:** 1GB+ (database büyütmesi için)
- **CPU:** Multi-core preferred

### Browser Support
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

---

## 🔧 Yerel Kurulum

### Step 1: Python Kontrolü
```bash
python --version
# Expected: Python 3.9.0 or higher
```

### Step 2: Bağımlılıklar
```bash
# requirements.txt (Recommended)
pip install -r requirements.txt
```

### Alternatif: Manuel Kurulum
```bash
pip install streamlit>=1.28.0
pip install pandas>=2.0.0
pip install numpy>=1.24.0
pip install plotly>=5.14.0
pip install openpyxl>=3.10.0
```

### Step 3: Veri Tabanı Hazırla
```bash
# app.py ilk çalıştırıldığında otomatik oluşturulur
# Veya manuel:
python -c "from database import db_manager; print('DB initialized')"
```

### Step 4: Uygulamayı Test Et
```bash
streamlit run app.py --logger.level=error
```

---

## 📁 Dosya Yapısı

```
tff_performans_sistemi/
├── app.py                          # Main Streamlit app
├── .streamlit/
│   └── config.toml                 # Streamlit configuration
├── pages/
│   ├── 01_Home.py                  # Ana sayfa
│   ├── 02_Kamp_Analizi.py          # Camp analysis
│   ├── 03_Oyuncu_Profili.py        # Player profiles
│   ├── 04_Karsilastirma.py         # Comparisons
│   ├── 05_Siralamalar.py           # Rankings
│   ├── 06_Scatter.py               # Scatter analysis
│   ├── 07_Oyuncu_Galerisi.py       # Player gallery
│   ├── 08_Istatistikler.py         # Statistics
│   ├── 09_Admin_Panel.py           # Admin panel
│   └── 10_Oyuncu_Arama.py          # Player search
├── Core Modules/
│   ├── database.py                 # Database layer (OPTIMIZED)
│   ├── utils.py                    # Utilities (OPTIMIZED)
│   ├── styles.py                   # Styling (OPTIMIZED)
│   ├── config.py                   # Configuration
│   ├── components.py               # UI Components
│   ├── analytics.py                # Analytics functions
│   └── export_tools.py             # Export utilities
├── tff_performans.db               # SQLite Database
├── requirements.txt                # Python dependencies
└── .gitignore                      # Git ignore file
```

---

## ⚙️ Konfigürasyon

### .streamlit/config.toml (YENİ)

Oluşturun: `.streamlit/config.toml`

```toml
[client]
showErrorDetails = false
showSidebarNavigation = true
toolbarMode = "viewer"
maxUploadSize = 200

[logger]
level = "warning"

[server]
headless = true
port = 8501
runOnSave = false
enableXsrfProtection = true
enableCORS = false
maxUploadSize = 200

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#E30A17"
backgroundColor = "#F9FAFB"
secondaryBackgroundColor = "#FFFFFF"
textColor = "#111827"
font = "sans serif"
```

### Environment Variables (Production)

```bash
# .env file
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_CLIENT_TOOLBAR_MODE=minimal
STREAMLIT_LOGGER_LEVEL=error
ADMIN_PASSWORD=your_secure_password_here
DATABASE_URL=tff_performans.db
```

### config.py İçinde Ayarlanabilir Parametreler

```python
# Sayfalar arası yüklemeler için optimizasyon
CACHE_TTL = 600  # 10 minutes

# DataFrame gösterim ayarları
DATAFRAME_KWARGS = {
    'use_container_width': True,
    'hide_index': True,
    'height': 500  # Performance için height sınırlandır
}

# Grafik ayarları
PLOTLY_CONFIG = {
    'responsive': True,
    'displayModeBar': False,  # Toolbar gizle (performance)
    'displaylogo': False
}
```

---

## 🌐 Streamlit Deployment

### Option 1: Streamlit Cloud (Recommended)

#### Adımlar:
1. GitHub'a push edin
2. [Streamlit Cloud](https://streamlit.io/cloud) ziyaret edin
3. "New App" → Repository seçin
4. Branch: `main`, Main file: `app.py`
5. Deploy

#### secrets.toml (Streamlit Cloud)
```toml
# Streamlit Cloud dashboard'da ayarlayın:
# Settings → Secrets
ADMIN_PASSWORD = "your_password"
DATABASE_URL = "tff_performans.db"
```

### Option 2: Heroku Deployment

#### Dosyalar:
**Procfile**
```
web: streamlit run app.py --server.port=$PORT
```

**runtime.txt**
```
python-3.10.13
```

#### Deploy:
```bash
heroku login
heroku create tff-performans
git push heroku main

# Logs kontrol et
heroku logs --tail
```

### Option 3: Docker Deployment

**Dockerfile**
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

**Build & Run:**
```bash
docker build -t tff-performans .
docker run -p 8501:8501 tff-performans
```

### Option 4: AWS/GCP/Azure

#### AWS EC2 örneği:
```bash
# Ubuntu 22.04 instance

# Python yükle
sudo apt update && sudo apt install python3.10 python3-pip

# Repository clone et
git clone <url>
cd tff_performans_sistemi

# Virtual env
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Streamlit çalıştır
nohup streamlit run app.py --server.port 80 &
```

---

## 🔐 Üretim Ortamı Ayarları

### 1. Security Checklist

- [ ] Admin panel passwordu güçlü
- [ ] HTTPS enabled (SSL certificate)
- [ ] CORS properly configured
- [ ] Input validation enabled
- [ ] SQL injection prevention (SQLite yapısı güvenli)
- [ ] CSRF protection enabled
- [ ] Error details gizlenmiş (showErrorDetails = false)

### 2. Performance Tuning

```python
# database.py
# Connection pooling (untuk high concurrency)
class DatabaseManager:
    def __init__(self, pool_size=5):
        self.pool_size = pool_size
        # Connection pool implementation
```

### 3. Monitoring Setup

#### Sentry Integration (Optional)
```python
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,
    environment="production"
)
```

#### Application Metrics
```python
# Track key metrics
- Page load times
- Cache hit ratios
- Database query times
- Error rates
```

### 4. Backup Strategy

```bash
#!/bin/bash
# Daily backup script

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
cp tff_performans.db $BACKUP_DIR/tff_performans_$DATE.db

# Keep last 30 days
find $BACKUP_DIR -name "*.db" -mtime +30 -delete

# Upload to cloud storage
aws s3 cp $BACKUP_DIR/tff_performans_$DATE.db s3://my-bucket/backups/
```

### 5. Logging Configuration

```python
# logging_config.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

---

## 🔄 Maintenance

### Weekly Tasks
- [ ] Database optimization
- [ ] Error log review
- [ ] Cache statistics check
- [ ] Backup verification

### Monthly Tasks
- [ ] Performance analysis
- [ ] Security audit
- [ ] User feedback review
- [ ] Update dependency versions

### Quarterly Tasks
- [ ] Major version updates
- [ ] Feature releases
- [ ] Documentation update
- [ ] Load testing

---

## 🆘 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'streamlit'"
```bash
pip install --upgrade streamlit
```

### Issue: "Database is locked"
```python
# database.py içinde
self.conn = sqlite3.connect(
    self.db_path, 
    timeout=20.0,  # Timeout artır
    check_same_thread=False
)
```

### Issue: "Out of Memory"
- Cache TTL'i azaltın
- DataFrame size'ını sınırlandırın
- Plotly rendering'ini optimize edin

### Issue: "Slow loading on Mobile"
- CSS media queries kontrol et
- Image sizes optimize et
- Lazy loading enabled mi?

---

## 📞 Support & Resources

### Yaygın Sorular

**Q: Çoklu kullanıcı desteklenmiyor mu?**  
A: Streamlit single-user framework'tür. Multi-user için alternatives:
- Dash (Plotly)
- Gradio
- FastAPI + Frontend

**Q: Database'i PostgreSQL'e değiştirebilir miyim?**  
A: Evet! `database.py`'de SQL dialect değiştirin

**Q: Production'da kaç concurrent users desteklenir?**  
A: Streamlit Cloud'da ~50 concurrent. Daha fazla için enterprise solution gerekir.

### Kontakt
- Documentation: `/docs`
- Issues: GitHub Issues
- Email: teknisyen@tff.org.tr

---

## ✅ Deployment Checklist

**Pre-Deployment:**
- [ ] Tüm tests pass
- [ ] Code review completed
- [ ] Database migration tested
- [ ] Performance benchmarks OK
- [ ] Security audit passed

**Deployment:**
- [ ] Backup alındı
- [ ] DNS configured
- [ ] SSL certificate valid
- [ ] Monitoring setup
- [ ] Team notified

**Post-Deployment:**
- [ ] Health checks passed
- [ ] User notifications sent
- [ ] Error logs monitored
- [ ] Performance metrics tracked
- [ ] Documentation updated

---

**Version:** 5.0 Optimized  
**Last Updated:** Feb 26, 2026  
**Status:** ✅ Production Ready

Kurulum ve deployment ile ilgili sorularınız için lütfen iletişime geçiniz.
