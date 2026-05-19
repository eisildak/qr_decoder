# 📷 QR Kod Okuyucu

> **İleri Programlama Dersi — Final Projesi**
> Python + OpenCV kullanarak gerçek zamanlı QR kod okuma uygulaması.

---

## 📌 Proje Hakkında

Bu proje, **Python** ve **OpenCV** kütüphanesi kullanılarak geliştirilmiş çok platformlu bir QR kod okuyucudur. Kamera görüntüsünden gerçek zamanlı olarak QR kodları tespit eder, içeriklerini çözümler ve ekranda gösterir. Aynı anda birden fazla QR kod okunabilir ve sonuçlar dosyaya kaydedilebilir.

Proje iki farklı mod ile çalışmaktadır:
- **Web Modu** — Flask tabanlı sunucu üzerinden tarayıcıda çalışır (masaüstü ve mobil)
- **Masaüstü Modu** — OpenCV penceresi ile doğrudan çalışır

---

## 🎯 Gereksinimler ve Kazanımlar

| Gereksinim | Açıklama | Durum |
|---|---|---|
| Kamera ile QR tespiti | OpenCV + pyzbar ile gerçek zamanlı tespit | ✅ |
| İçerik çözümleme | URL, metin, vCard vb. tüm QR içerikleri | ✅ |
| Çoklu QR okuma | Aynı karede birden fazla QR kod desteği | ✅ |
| Dosyaya kayıt | CSV ve TXT formatında otomatik kayıt | ✅ |
| Web arayüzü | Flask + HTML5 responsive tasarım | ✅ |
| Mobil uyumluluk | Telefon tarayıcısından erişim | ✅ |

**Kazanımlar:**
- Görüntüden veri çıkarımı (image processing)
- Kod çözme (decoding) işlemleri
- Gerçek zamanlı analiz
- Flask ile REST API geliştirme
- Web/mobil entegrasyon

---

## 🗂️ Proje Yapısı

```
qr_reader/
│
├── qr_detector.py      # Çekirdek modül: OpenCV + pyzbar QR tespit motoru
├── logger.py           # CSV ve TXT kayıt modülü (duplicate filtreleme dahil)
├── app.py              # Flask web sunucusu ve REST API endpoint'leri
├── desktop.py          # Masaüstü modu: OpenCV penceresi ile çalışır
├── run.sh              # Tek komutla başlatıcı script
├── requirements.txt    # Python bağımlılıkları
│
├── templates/
│   └── index.html      # Web arayüzü (mobil responsive)
│
├── static/
│   ├── style.css       # Koyu tema, mobil uyumlu tasarım
│   └── app.js          # Kamera yönetimi, API iletişimi, canvas çizimi
│
└── logs/               # Otomatik oluşur
    ├── qr_log_YYYYMMDD.csv
    └── qr_log_YYYYMMDD.txt
```

---

## ⚙️ Kurulum

### 1. Gerekli sistem kütüphanesi (macOS)
```bash
brew install zbar
```

### 2. Sanal ortam oluştur ve bağımlılıkları kur
```bash
cd qr_reader
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Çalıştır
```bash
chmod +x run.sh

# Web modu (tarayıcı + mobil)
./run.sh web

# Masaüstü modu (OpenCV penceresi)
./run.sh desktop
```

---

## 🚀 Kullanım

### 🌐 Web Modu

```bash
./run.sh web
```

Sunucu başladıktan sonra:

- **Bilgisayar:** `https://localhost:5050`
- **Telefon (aynı Wi-Fi):** `https://192.168.x.x:5050`

> ⚠️ **Not:** Tarayıcıda "Güvenli değil" uyarısı çıkabilir. Bu, self-signed sertifika kullandığımız için normaldir. "Gelişmiş → Devam et" seçeneğiyle geçin. HTTPS zorunludur çünkü mobil tarayıcılar kamera iznini yalnızca güvenli bağlantıda verir.

**Web arayüzü özellikleri:**
- Kamerayı aç / kapat
- Birden fazla kamera seçimi
- Mobilde ön/arka kamera değiştirme
- Tespit edilen kodları anlık listeleme
- URL ise tıklanabilir link
- Geçmiş tablosu
- CSV ve TXT olarak dışa aktarma

### 🖥️ Masaüstü Modu

```bash
./run.sh desktop
# veya farklı kamera için:
./run.sh desktop --camera 1
```

- `q` tuşu ile çıkılır
- Tespit edilen kodlar terminale yazdırılır ve `logs/` klasörüne kaydedilir

---

## 🔌 API Endpoint'leri

| Method | Endpoint | Açıklama |
|---|---|---|
| `POST` | `/api/decode` | Base64 görüntü alır, QR sonuçlarını JSON döner |
| `GET` | `/api/history` | Oturumda kaydedilen tüm QR kodları |
| `GET` | `/api/export/csv` | CSV dosyasını indir |
| `GET` | `/api/export/txt` | TXT dosyasını indir |

**Örnek istek:**
```json
POST /api/decode
{
  "image": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**Örnek yanıt:**
```json
{
  "results": [
    {
      "data": "https://erolisildak.com",
      "type": "QRCODE",
      "timestamp": "2026-05-20 13:45:22"
    }
  ],
  "count": 1,
  "total_saved": 5
}
```

---

## 📁 Kayıt Formatları

### CSV (`logs/qr_log_YYYYMMDD.csv`)
```
timestamp,type,data,session_id
2026-05-20 13:45:22,QRCODE,https://erolisildak.com,134500
2026-05-20 13:45:35,CODE128,1234567890,134500
```

### TXT (`logs/qr_log_YYYYMMDD.txt`)
```
[2026-05-20 13:45:22] [QRCODE] https://erolisildak.com
[2026-05-20 13:45:35] [CODE128] 1234567890
```

> Aynı QR kod oturum boyunca bir kez kaydedilir (duplicate filtreleme).

---

## 🛠️ Kullanılan Teknolojiler

| Teknoloji | Versiyon | Amaç |
|---|---|---|
| Python | 3.9+ | Ana programlama dili |
| OpenCV (`opencv-python`) | 4.9+ | Kamera akışı ve görüntü işleme |
| pyzbar | 0.1.9+ | QR / barkod çözümleme motoru |
| Flask | 3.0+ | Web sunucusu ve REST API |
| pyOpenSSL | 24.0+ | HTTPS / self-signed sertifika |
| HTML5 / JavaScript | — | Web arayüzü ve kamera erişimi |
| zbar (sistem) | — | pyzbar'ın bağımlı olduğu C kütüphanesi |

---

## 🏗️ Mimari

```
Tarayıcı (Mobil / Web)
    │
    │  getUserMedia API → kamera frame'i yakala
    │  Her 200ms'de base64 JPEG → POST /api/decode
    │
    ▼
Flask Sunucusu (app.py)
    │
    │  base64 → numpy array (OpenCV)
    │
    ▼
QRDetector (qr_detector.py)
    │
    │  pyzbar.decode() → tüm QR / barkodları bul
    │  Koordinatları ölçekle, QRResult nesnesi oluştur
    │
    ▼
QRLogger (logger.py)
    │
    │  Duplicate filtrele → CSV + TXT'e yaz
    │
    ▼
JSON yanıt → Tarayıcıya gönder → Ekranda göster
```

---

## 📋 Geliştirme Notları

- `QRDetector.detect_image()` statik metod olduğu için hem Flask API hem masaüstü modu aynı çekirdek kodu kullanır.
- `scale` parametresi düşük güçlü cihazlarda frame küçülterek performansı artırır (örn. `--scale 0.5`).
- Oturum bazlı duplicate filtreleme `set()` veri yapısıyla O(1) karmaşıklıkla çalışır.
- Flask `ssl_context='adhoc'` ile her başlatmada yeni geçici sertifika üretir — üretim ortamı için kalıcı sertifika önerilir.

---

## 👤 Geliştirici

**Erol Işıldak**
İleri Programlama Dersi — Final Projesi
# qr_decoder
