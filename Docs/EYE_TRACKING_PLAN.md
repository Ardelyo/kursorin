# 👁️ RENCANA IMPLEMENTASI MOUSE PELACAK MATA (EYE TRACKING)

## 📋 Ringkasan Eksekutif

Mengembangkan sistem kontrol kursor berbasis pelacakan mata yang presisi, responsif, dan mudah digunakan, dirancang khusus untuk membantu pengguna dengan keterbatasan mobilitas fisik. Sistem ini menggunakan webcam standar dan algoritma AI canggih untuk menerjemahkan gerakan mata menjadi gerakan kursor yang akurat.

## 🎯 Fitur Utama

### 1. Sistem Kalibrasi Intuitif ("Lihat Titik")
Agar pelacakan mata akurat, sistem perlu mempelajari karakteristik mata pengguna.
- **Proses Kalibrasi 9-Titik**: Pengguna diminta melihat titik-titik yang muncul secara berurutan di layar (sudut, tengah, sisi).
- **Validasi Real-time**: Sistem memberikan umpan balik visual (misal: lingkaran berubah warna) saat data mata berhasil ditangkap untuk titik tersebut.
- **Kalibrasi Ulang Cepat**: Opsi untuk kalibrasi ulang cepat jika akurasi menurun tanpa harus mengulang proses penuh.
- **Profil Pengguna**: Menyimpan data kalibrasi untuk berbagai pengguna atau kondisi pencahayaan berbeda.

### 2. Fitur Aksesibilitas Komprehensif
Dirancang untuk berbagai jenis disabilitas:
- **Mode Hands-Free Total**:
    - **Klik Dwell (Diam)**: Klik otomatis saat pengguna menatap satu titik selama durasi tertentu (bisa diatur).
    - **Klik Kedipan**: Klik kiri dengan kedipan mata kiri, klik kanan dengan kedipan mata kanan (opsional/dapat dikonfigurasi).
- **Mode Hibrida (Mata + Suara)**:
    - Gunakan mata untuk mengarahkan kursor.
    - Gunakan perintah suara ("Klik", "Scroll", "Drag") untuk aksi.
- **Stabilisasi Tremor Mata**: Algoritma smoothing canggih untuk menyaring gerakan mata mikro yang tidak disengaja (saccades) agar kursor tetap stabil.
- **Interface Kontras Tinggi**: UI kalibrasi dan pengaturan yang mudah dilihat bagi pengguna dengan gangguan penglihatan (low vision).

### 3. Kompatibilitas Lintas Platform (Cross-Platform)
Sistem dibangun agar bisa berjalan di berbagai sistem operasi:
- **Windows, macOS, Linux**: Menggunakan Python sebagai bahasa inti.
- **Abstraksi Input**: Menggunakan library seperti `PyAutoGUI` atau `pynput` yang bekerja di semua OS utama untuk mengontrol mouse sistem.
- **Dependensi Ringan**: Mengandalkan `OpenCV` dan `MediaPipe` yang didukung luas di berbagai platform.

## 🏗️ Arsitektur Teknis

```
┌─────────────────────────────────────────────────────────────┐
│                 PIPELINE PELACAKAN MATA                     │
├─────────────────────────────────────────────────────────────┤
│  1. Input Webcam                                            │
│     ↓                                                       │
│  2. Deteksi Wajah & Landmark (MediaPipe Face Mesh)          │
│     ↓                                                       │
│  3. Ekstraksi Wilayah Mata & Iris                           │
│     ↓                                                       │
│  4. Estimasi Arah Pandangan (Gaze Estimation)               │
│     ↓                                                       │
│  5. Pemetaan ke Layar (Screen Mapping + Kalibrasi)          │
│     ↓                                                       │
│  6. Smoothing & Stabilisasi (Kalman Filter / Moving Avg)    │
│     ↓                                                       │
│  7. Kontrol Mouse Sistem (PyAutoGUI)                        │
└─────────────────────────────────────────────────────────────┘
```

## 📈 Peta Jalan Implementasi

### **Fase 1: Prototipe Dasar (Minggu 1-2)**
- [ ] Setup lingkungan pengembangan (Python, OpenCV, MediaPipe).
- [ ] Implementasi deteksi iris mata real-time.
- [ ] Implementasi logika pemetaan koordinat mata ke layar dasar.

### **Fase 2: Sistem Kalibrasi (Minggu 3-4)**
- [ ] Buat UI kalibrasi 9-titik.
- [ ] Implementasi algoritma transformasi koordinat berdasarkan data kalibrasi.
- [ ] Simpan/muat profil kalibrasi.

### **Fase 3: Penyempurnaan & Aksesibilitas (Minggu 5-6)**
- [ ] Tambahkan algoritma smoothing untuk mengurangi jitter.
- [ ] Implementasi fitur Dwell Click dan Blink Click.
- [ ] Tambahkan GUI pengaturan sensitivitas dan timing.

### **Fase 4: Pengujian & Optimasi (Minggu 7-8)**
- [ ] Uji coba pada berbagai kondisi pencahayaan.
- [ ] Optimasi penggunaan CPU/RAM.
- [ ] Pengujian pengguna dengan berbagai skenario disabilitas.

## 🔧 Spesifikasi Kebutuhan

- **Hardware**: Webcam standar (720p disarankan), Prosesor i3 gen 5 ke atas atau setara.
- **Software**: Python 3.8+, Library: `opencv-python`, `mediapipe`, `pyautogui`, `numpy`, `scipy`.

## 🎯 Metrik Keberhasilan

- **Akurasi**: Kursor berada dalam radius 50 pixel dari target yang dilihat pengguna.
- **Waktu Kalibrasi**: Proses kalibrasi selesai di bawah 1 menit.
- **Kenyamanan**: Pengguna dapat menggunakan sistem selama 30 menit tanpa kelelahan mata yang signifikan (berkat smoothing yang baik).
