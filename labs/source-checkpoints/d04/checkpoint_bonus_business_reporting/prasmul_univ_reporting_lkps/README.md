# Laporan Finansial LKPS Parsial

Menghasilkan workbook persiapan dari jurnal accounting yang sudah diposting.
Laporan memakai periode kalender aktual dan menandai secara terbuka mapping yang
masih harus ditinjau.

Sheet sumber menampilkan distribusi analitik standar Odoo sebagai dimensi organisasi
yang tersedia. Laporan tidak menganggap sebuah akun analitik pasti merupakan program
studi.

Addon ini tidak menyediakan indikator mahasiswa, dosen, lulusan, luaran penelitian,
pengabdian kepada masyarakat, atau indikator akreditasi nonfinansial lainnya.

## Cara kerja singkat

1. Pengguna memilih company serta tanggal awal dan akhir pada wizard.
2. ORM mencari ID jurnal yang boleh dibaca pengguna sesuai record rule.
3. Raw SQL hanya mengambil ringkasan dari ID jurnal hasil pencarian ORM tersebut.
4. Python mengelompokkan nama akun ke kategori finansial LKPS sementara.
5. Workbook menampilkan ringkasan, mapping, data sumber, dan kontrol.

## Isi workbook

- `Finansial LKPS`: ringkasan nominal per kategori dan tahun kalender aktual.
- `Mapping & Cakupan`: daftar akun serta status keandalan mapping.
- `Data Sumber`: rincian agregasi akun yang menjadi sumber ringkasan.
- `Kontrol`: angka kontrol untuk membantu pemeriksaan hasil.

## Istilah penting

- **LKPS** adalah Laporan Kinerja Program Studi untuk kebutuhan akreditasi. Addon
  ini hanya menangani bagian finansial yang tersedia dalam database accounting.
- **TS** adalah tahun akademik penuh terakhir yang dipakai dalam pelaporan LKPS.
  `TS-1` dan `TS-2` adalah satu dan dua tahun sebelum TS. Contoh ini belum
  menetapkannya karena database hanya menyediakan rentang tanggal aktual.
- **ORM** adalah cara standar Odoo membaca model dengan tetap memakai mekanisme
  akses Odoo.
- **Raw SQL** adalah query langsung ke PostgreSQL. Query pada addon ini memakai
  parameter terpisah agar nilai filter tidak digabungkan ke teks SQL.
- **Record rule** adalah aturan Odoo yang membatasi record mana yang boleh dilihat
  pengguna. ID jurnal dicari lewat ORM lebih dahulu agar batas ini tetap berlaku.
- **Posted** berarti jurnal sudah dikonfirmasi dan masuk pencatatan accounting.
  Jurnal draft tidak dimasukkan.
- **Jenis akun** adalah klasifikasi bawaan Odoo seperti pendapatan, biaya, atau
  aset tetap. Nilai ini membantu query memilih jurnal yang relevan.
- **Mapping** adalah aturan yang menghubungkan akun accounting dengan kategori
  laporan LKPS.
- **Coverage** menunjukkan seberapa banyak data yang tersedia dan bagian mana yang
  masih perlu diperiksa.
- **Perlu Ditinjau** berarti mapping dibuat dari kata pada nama akun dan belum boleh
  dianggap final tanpa konfirmasi pengguna bisnis.
- **Distribusi analitik** adalah pembagian nilai jurnal ke akun analitik, misalnya
  cost center atau unit kerja. Addon tidak menganggapnya otomatis sebagai prodi.
- **Rekonsiliasi** adalah proses membandingkan hasil laporan dengan data sumber
  untuk memastikan jumlahnya dapat dijelaskan.
