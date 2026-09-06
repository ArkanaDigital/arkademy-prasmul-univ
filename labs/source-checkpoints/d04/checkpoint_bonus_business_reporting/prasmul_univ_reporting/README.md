# Pelaporan Universitas Prasmul

Fondasi bersama untuk laporan bisnis kustom pada project pelatihan.

Addon ini menyediakan grup akses pelaporan serta bantuan XLSX yang dapat digunakan
kembali. Laporan untuk kebutuhan bisnis tertentu ditempatkan dalam addon terpisah
yang bergantung pada modul ini.

Berikan grup **Pengguna Business Reporting** kepada pengguna sebelum mereka membuka
menu laporan.

## Cara kerja singkat

1. Install addon ini terlebih dahulu.
2. Berikan grup **Pengguna Business Reporting** kepada pengguna yang boleh mencetak
   laporan.
3. Install addon laporan yang membutuhkan fondasi ini.
4. Menu setiap addon laporan tersedia pada
   **Accounting → Reporting → Business Reporting**.

## Istilah penting

- **Addon** adalah satu paket fitur Odoo yang memiliki manifest, kode Python,
  keamanan, dan tampilan sendiri.
- **Dependency** adalah addon lain yang harus sudah tersedia agar sebuah addon
  dapat di-install.
- **XLSX** adalah format file workbook yang umum dibuka menggunakan Microsoft
  Excel, LibreOffice Calc, atau aplikasi spreadsheet lain.
- **Helper** adalah method bantuan untuk menghindari penulisan kode yang sama pada
  banyak laporan.
- **Mixin** adalah model bantuan yang mewariskan method kepada model lain. Mixin
  ini tidak mempunyai menu atau tabel bisnis sendiri.
- **Transient wizard** adalah form sementara untuk menerima filter pengguna.
  Datanya akan dibersihkan otomatis oleh Odoo setelah tidak lagi diperlukan.
- **Field binary** adalah field Odoo yang menyimpan isi file dalam bentuk data
  biner agar file dapat diunduh dari wizard.
- **Company** adalah entitas perusahaan atau organisasi pada fitur multi-company
  Odoo. Filter ini mencegah data beberapa entitas tercampur dalam satu laporan.
