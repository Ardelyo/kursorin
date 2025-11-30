# RENCANA PEROMBAKAN TOTAL PROYEK KURSORIN

## 🎯 Tujuan Utama
1.  **Penyederhanaan Struktur**: Mengurangi kedalaman folder yang tidak perlu.
2.  **Fokus Fungsionalitas**: Menegaskan kemampuan saat ini (Pelacakan Kepala & Tangan).
3.  **Open Source Friendly**: Membuat proyek mudah dipahami dan dikontribusikan oleh orang lain.
4.  **Pembersihan**: Menghapus file sampah, log, dan kode legacy yang tidak terpakai.

## 📂 Struktur Folder Saat Ini (Berantakan)
```
kursorin/
├── Current_Version/
│   ├── Core/
│   │   └── modules/ (Terlalu dalam)
│   ├── Config/
│   ├── Docs/
│   ├── Legacy_Code/ (Sampah)
│   └── ...
├── Archive/ (Sampah)
├── Tools/ (Bisa disatukan)
└── ...
```

## ✨ Struktur Folder Baru (Diusulkan)
Kita akan memindahkan isi `Current_Version` ke root utama (atau folder `src` baru) dan meratakan strukturnya.

```
kursorin/
├── src/                    # Kode Sumber Utama
│   ├── trackers/           # Modul pelacakan (Head, Hand)
│   │   ├── head_tracker.py
│   │   └── hand_tracker.py
│   ├── ui/                 # Antarmuka Pengguna (GUI)
│   ├── utils/              # Fungsi bantuan & tools
│   └── main.py             # Entry point aplikasi
├── config/                 # Konfigurasi (JSON)
├── docs/                   # Dokumentasi (PANDUAN, RENCANA)
├── assets/                 # Ikon, Gambar
├── tests/                  # Pengujian
├── run.bat                 # Script peluncur Windows (Gabungan START.bat)
├── launch.py               # Script peluncur Python
├── requirements.txt        # Daftar dependensi
├── README.md               # Dokumentasi Utama (Indonesian)
├── CONTRIBUTING.md         # Panduan Kontribusi
├── LICENSE                 # Lisensi (MIT)
└── .gitignore              # Git ignore file
```

## 📝 Langkah Implementasi Detail

### 1. Persiapan & Backup
- [ ] Pastikan semua perubahan kode tersimpan.
- [ ] Buat backup folder `Current_Version` jika perlu (opsional, karena ada git).

### 2. Pembersihan (Cleanup)
- [ ] Hapus folder `Legacy_Code` di dalam `Current_Version`.
- [ ] Hapus folder `Archive` di root.
- [ ] Hapus folder `Logs` (akan digenerate ulang saat run).
- [ ] Hapus folder `__pycache__` di semua tempat.

### 3. Restrukturisasi (Pindah & Ratakan)
- [ ] Buat folder `src`, `config`, `docs`, `assets`, `tests` di root `kursorin`.
- [ ] Pindahkan isi `Current_Version/Core/modules/*` ke `src/`. (Perlu penyesuaian import).
- [ ] Pindahkan `Current_Version/Config/*` ke `config/`.
- [ ] Pindahkan `Current_Version/Docs/*` dan file .md di root ke `docs/`.
- [ ] Pindahkan `Current_Version/Assets/*` ke `assets/`.
- [ ] Pindahkan `Tools/*` yang berguna ke `src/utils/` atau `tests/`.
- [ ] Pindahkan `launch.py` dan `requirements.txt` ke root `kursorin`.

### 4. Penyesuaian Kode (Refactoring)
- [ ] Perbaiki semua path import di file Python karena perubahan struktur folder.
- [ ] Pastikan `launch.py` menunjuk ke lokasi `src/main.py` (atau entry point yang sesuai) yang baru.
- [ ] Perbarui path konfigurasi di kode agar membaca dari folder `config/`.

### 5. Dokumentasi & Finalisasi
- [ ] Update `README.md` di root dengan informasi terbaru, cara instalasi, dan fitur (Head & Hand Tracking).
- [ ] Buat `CONTRIBUTING.md` dengan panduan ramah untuk kontributor.
- [ ] Buat `.gitignore` untuk mengabaikan `__pycache__`, `*.log`, `.env`, dll.
- [ ] Hapus folder `Current_Version` yang sudah kosong.

## 🚀 Hasil Akhir
Proyek akan terlihat profesional, bersih, dan siap untuk kolaborasi open source.
