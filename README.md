# 🖱️ Kursorin: Kontrol Kursor Pintar (Head & Hand Tracking)

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

**Kursorin** adalah aplikasi open-source yang memungkinkan Anda mengontrol kursor mouse komputer menggunakan gerakan kepala dan tangan. Dirancang untuk aksesibilitas dan kemudahan penggunaan tanpa perangkat keras khusus—hanya webcam standar.

## ✨ Fitur Utama

- **👁️ Pelacakan Kepala (Head Tracking)**: Gerakkan kursor dengan menolehkan kepala. Cocok untuk pengguna dengan keterbatasan mobilitas tangan.
- **🖐️ Pelacakan Tangan (Hand Tracking)**: Kontrol kursor dan klik menggunakan gestur tangan intuitif.
- **🚀 Ringan & Cepat**: Dibangun dengan Python dan dioptimalkan untuk performa tinggi.
- **♿ Fokus Aksesibilitas**: Dirancang untuk membantu pengguna difabel mengoperasikan komputer dengan mandiri.

## 📁 Struktur Proyek

Proyek ini telah direstrukturisasi agar lebih rapi dan mudah dikembangkan:

```
kursorin/
├── src/                # Kode sumber utama
│   ├── trackers/       # Modul pelacakan (Head, Hand)
│   ├── ui/             # Antarmuka Pengguna (GUI)
│   └── utils/          # Utilitas sistem
├── config/             # File konfigurasi
├── docs/               # Dokumentasi lengkap
├── assets/             # Aset visual
└── tests/              # Unit testing
```

## 🚀 Cara Memulai

### Prasyarat
- Python 3.8 atau lebih baru
- Webcam yang berfungsi

### Instalasi

1.  **Clone repositori ini:**
    ```bash
    git clone https://github.com/username/kursorin.git
    cd kursorin
    ```

2.  **Instal dependensi:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Jalankan aplikasi:**
    ```bash
    python launch.py
    ```

## 📖 Dokumentasi

- [Panduan Folder](docs/FOLDER_GUIDE.md)
- [Rencana Mode Gaming](docs/GAMING_MODE_PLAN.md)
- [Rencana Mode Mengetik](docs/TYPING_MODE_PLAN.md)
- [Rencana Eye Tracking](docs/EYE_TRACKING_PLAN.md)

## 🤝 Berkontribusi

Kami sangat menyambut kontribusi dari komunitas! Silakan baca [CONTRIBUTING.md](CONTRIBUTING.md) untuk panduan cara berkontribusi.

## 📄 Lisensi

Proyek ini dilisensikan di bawah lisensi MIT. Lihat file [LICENSE](LICENSE) untuk detailnya.
