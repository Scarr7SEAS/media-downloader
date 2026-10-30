# ⚡ Universal Media Downloader (YouTube & TikTok)

Aplikasi downloader video YouTube dan TikTok dengan antarmuka Web modern (FastAPI + Vanilla JS), mendukung pilihan kualitas, ekstraksi MP3, dan optimasi codec agar **100% kompatibel di semua platform** (WhatsApp, iOS/iPhone, Android, macOS, dan Windows).

---

## ✨ Fitur Utama

1. **Dukungan Platform Lengkap**:
   - YouTube (Video reguler, Shorts, live replay, 4K/60fps HDR).
   - TikTok (Video vertikal HD, suara asli).
2. **3 Pilihan Kualitas Dinamis**:
   - 📱 **Kualitas Sedang (720p)**: Ukuran file ringkas, hemat kuota, pas untuk dikirim via WhatsApp/chat tanpa kompresi berat.
   - 🎬 **Kualitas Penuh (Original Max - Hingga 4K 60fps)**: Mengambil format video dan framerate tertinggi dari sumber video asli tanpa downscaling resolusi.
   - 🎵 **Hanya Audio (MP3)**: Ekstrak audio jernih standar MP3 192 kbps.
3. **Kompatibilitas Universal & Bit-Exact Streaming**:
   - Jika sumber sudah H.264 + AAC + YUV420p, file disalin bit-for-bit (`-c copy`) tanpa kompresi ulang.
   - Jika sumber menggunakan VP9/AV1 (misal YouTube 4K 60fps), video ditranskode ke H.264 dengan profil visual lossless (CRF 17) tetap mempertahankan resolusi asli 4K dan 60fps.
   - Dilengkapi flag **`-movflags +faststart`** agar video bisa langsung diputar saat di-streaming atau dikirim di WhatsApp/Telegram tanpa harus selesai unduh seutuhnya.
4. **Antarmuka Web Modern (Full SVG Icons)**:
   - Desain profesional menggunakan ikon vektor SVG modern (Lucide SVG style, tanpa emoji).
   - Pratinjau thumbnail, durasi, uploader, dan deteksi resolusi tertinggi (misal: "4K Ultra HD (2160p) 60fps").
   - Indikator progres realtime (persentase, kecepatan unduh, sisa waktu).
   - Pemutar video/audio langsung di browser (inline preview).
   - Riwayat unduhan lokal dengan tombol aksi langsung.

---

## 🚀 Cara Menjalankan

### Cara 1: Menggunakan Script Otomatis (Windows)
Cukup **klik ganda (double-click)** file `start.bat`. Browser akan terbuka otomatis di `http://127.0.0.1:8000`.

### Cara 2: Lewat Terminal / Command Prompt
```bash
# Masuk ke direktori proyek
cd "C:\Users\LENOVO LOQ 15\Project Gabut"

# Jalankan server
.\.venv\Scripts\python run.py
```

Buka browser dan akses:
👉 **`http://127.0.0.1:8000`**

---

## 📁 Struktur Proyek

```
Project Gabut/
├── .venv/                   # Virtual environment Python
├── app/
│   ├── __init__.py
│   ├── config.py            # Konfigurasi path & port
│   ├── downloader.py        # Core yt-dlp & FFmpeg universal compatibility
│   ├── main.py              # Server FastAPI & API endpoints
│   ├── static/
│   │   ├── css/style.css    # Gaya UI modern & responsif
│   │   └── js/app.js        # Logika interaktif frontend & live polling
│   └── templates/
│       └── index.html       # Tampilan web utama
├── downloads/               # Folder penyimpanan media yang sudah diunduh
├── requirements.txt         # Daftar pustaka Python
├── run.py                   # Script peluncur server
├── start.bat                # Shortcut klik-ganda Windows
└── README.md                # Dokumentasi proyek
```

---

## ⚙️ Persyaratan Sistem

- **Python 3.10+** (Sudah terpasang di `.venv`)
- **FFmpeg** (Sudah terdeteksi dan terintegrasi otomatis)
- **Node.js** (Opsional, untuk menyelesaikan tantangan JavaScript pada YouTube)
