# Admin Rehberi

## 🔐 Giriş

```
Şifre: tff2024
```

## 👤 Oyuncu Yönetimi

### Fotoğraf Yükleme
1. Admin Panel → "Oyuncular" sekmesi
2. "Fotoğraf Yükle" butonuna tıkla
3. Oyuncu adı seç
4. PNG/JPG/WEBP seç (max 5MB)
5. Kaydet

### Profil Düzenlemesi
- Jersey Numarası
- Pozisyon (GK/DEF/MID/FWD)
- Kulüp
- İletişim bilgileri

## ⚽ Kamp Yönetimi

### Kamp Oluşturma
1. "Kamplar" sekmesi
2. "Yeni Kamp" tıkla
3. Bilgileri gir:
   - Adı: "Ocak 2026 Kampı"
   - Yaş Grubu: 91U
   - Başlangıç: 01.02.2026
   - Bitiş: 15.02.2026
   - Konum: İstanbul

### Logo Yükleme
1. Kamp seçilir
2. Logo PNG/JPG yükle
3. Raporlarda otomatik görünür

## 🎨 Sistem Ayarları

### Renk Şeması
- Ana: TFF Kırmızı (#E30A17)
- İkinci: TFF Siyah (#1A1A1A)

### Hesaplama Parametreleri
- Percentile metodolojisi
- Bileşik skor ağırlıkları
- Anomali eşikleri
- Trend hesaplama

### Genel Ayarlar
- Sistem başlığı
- Footer metni
- Log tutma
- Backup sıklığı

## 📋 Audit Log

### İzlenen İşlemler
- Veri yükleme (kim, ne zaman, kaç satır)
- Oyuncu düzenleme
- Kamp oluşturma
- Rapor İndirme
- Admin işlemleri

### Log Görüntüleme
1. "Log" sekmesi
2. Son 100 işlem gösterilir
3. Filtreleme yapılabilir:
   - Tarih aralığı
   - İşlem türü
   - Kullanıcı

### Log Silme
- 90 günden eski loglar otomatik silinir
- Manuel silme: Admin onayı gerekli

## 🛡️ Güvenlik

### Kullanıcı Yönetimi
```python
# Admin panelinde şifre değiştirme
Admin Panel → Ayarlar → Şifre
```

### İzinler
```
ADMIN: Tüm erişim
COACH: Kendi kampını görebilir
VIEWER: Sadece okuma
PUBLIC: Paylaşılan link
```

### Oturum Güvenliği
- 30 dakika inaktivite → otomatik logout
- Her giriş kaydedilir
- IP adresi kontrol edilir

## 💾 Backup

### Otomatik Backup
- Günlük: Veritabanı + fotoğraflar
- Haftalık: Tüm + ZIP

### Manuel Backup
```
Admin Panel → Ayarlar → Backup Al
```

### Geri Yükleme
```
Admin Panel → Ayarlar → Geri Yükle
- Tarih seç
- Onayla
- Sistem yeniden başlar
```

## 🐛 Hata Giderme

### Sorun: Fotoğraf yüklenemedi
- Dosya boyutu 5MB'den büyük mü?
- Format PNG/JPG/WEBP mi?
- İnternet bağlantısı var mı?

### Sorun: Admin şifresi çalışmıyor
- Caps Lock kapalı mı?
- Boşluk var mı?
- "tff2024" tam yazıldı mı?

### Sorun: Log görünmüyor
- Veri tabanında log kaydı var mı?
- Zaman ayarları doğru mu?
- Sayfa yenile (F5)

## 📞 İleti

Sorunlar için: support@tff.org.tr
