# Bonus — Business Reporting

Checkpoint ini merupakan contoh lanjutan setelah peserta memahami wizard dan
export Excel pada Day 4. Materi ini bersifat referensi untuk menghadapi pola kerja
project nyata dan tidak wajib diselesaikan seluruhnya di kelas.

## Isi checkpoint

```text
prasmul_univ_reporting          fondasi keamanan dan helper XLSX
prasmul_univ_reporting_lkps     contoh laporan finansial LKPS parsial
prasmul_univ_reporting_tax      contoh laporan operasional pajak
```

Ketiga folder di atas adalah addon Odoo yang berdiri sendiri. Addon LKPS dan pajak
membutuhkan addon core `prasmul_univ_reporting`.

## Contoh output

Folder `contoh-output/` berisi hasil XLSX dari database pelatihan untuk periode
2026-05-01 sampai 2026-05-30:

- `LKPS_Parsial_Universitas_Prasetiya_Mulya_20260501_20260530.xlsx`
- `Pajak_Operasional_Universitas_Prasetiya_Mulya_20260501_20260530.xlsx`

Gunakan file ini untuk mengenali struktur sheet dan membandingkan hasil export
peserta. File tersebut adalah contoh pembelajaran, bukan dokumen pelaporan resmi.

## Urutan instalasi

1. Salin ketiga folder ke direktori yang tercantum dalam `addons_path`.
2. Restart Odoo dan pilih **Update Apps List**.
3. Install **Pelaporan Universitas Prasmul**.
4. Install addon LKPS parsial dan/atau operasional pajak.
5. Berikan grup **Pengguna Business Reporting** kepada pengguna.
6. Pastikan pengguna juga memiliki hak baca Accounting.
7. Buka menu **Accounting → Reporting → Business Reporting**, lalu pilih
   **LKPS Parsial** atau **Laporan Pajak**.

## Hubungan dengan materi Day 1–4

- Manifest, dependency, action, dan menu mengulang materi Day 1.
- Grup dan ACL mengulang materi Day 3.
- `TransientModel`, filter tanggal, file binary, dan XLSX mengulang materi Day 4.
- ORM digunakan untuk validasi dan angka kontrol.
- Raw SQL ditempatkan dalam method khusus dan memakai parameter binding, seperti
  variasi worksheet SQL pada Day 4.

## Alur yang perlu dipahami peserta

```text
Menu → Action → Wizard → Validasi ORM → Query SQL → Workbook XLSX → Download
```

- **ORM** adalah API model Odoo. Pada contoh ini ORM menjaga filter, hak akses, dan
  angka kontrol.
- **Raw SQL** adalah query langsung ke PostgreSQL. Parameter binding berarti nilai
  company/tanggal dikirim terpisah dari teks SQL agar lebih aman.
- **Workbook** adalah satu file Excel yang dapat memiliki beberapa sheet.
- **Rekonsiliasi** adalah proses membandingkan ringkasan dengan data sumber agar
  angka dapat ditelusuri.

## Batas contoh LKPS

LKPS adalah Laporan Kinerja Program Studi untuk kebutuhan akreditasi. Addon contoh
hanya mengolah bagian finansial yang tersedia dari jurnal accounting. Data
mahasiswa, dosen, lulusan, penelitian, PkM, dan indikator nonfinansial lain tidak
dibuat secara asumtif.

Status `Perlu Ditinjau` berarti kategori akun masih berdasarkan kata pada nama akun
dan harus dikonfirmasi oleh pengguna bisnis. Distribusi analitik ditampilkan sebagai
dimensi yang tersedia, tetapi tidak dianggap otomatis sebagai program studi.

## Batas contoh pajak

Workbook pajak ditujukan untuk pemeriksaan operasional. Hasilnya bukan SPT, bukti
potong, e-Faktur, atau dokumen Coretax resmi. Debit, kredit, saldo bersih, serta
nominal absolut ditampilkan terpisah supaya refund dan reversal dapat dikenali.

## Ide latihan ringan

Peserta dapat menyalin salah satu addon laporan lalu mengganti:

1. nama model, action, dan menu;
2. field filter pada wizard;
3. domain ORM atau query SQL;
4. judul serta kolom workbook;
5. nama file hasil download.

Target yang realistis untuk pemula adalah satu addon dapat di-install, menampilkan
wizard, dan menghasilkan workbook sederhana. Mapping LKPS dan rekonsiliasi pajak
yang lengkap cukup dipelajari sebagai referensi lanjutan.

## Checklist pengujian

Skenario uji utama pada database pelatihan `v18_prasmul_dev` menggunakan periode
**2026-05-01** sampai **2026-05-31** untuk LKPS Parsial dan Laporan Pajak. Mei
2026 dipilih karena hasil pajaknya memiliki 535 baris: cukup kaya untuk ditinjau,
namun tidak sebesar satu tahun penuh.

- [ ] Ketiga addon dapat di-install tanpa mengubah source Odoo.
- [ ] LKPS Parsial berhasil diekspor untuk periode 2026-05-01 s.d. 2026-05-31.
- [ ] Laporan Pajak berhasil diekspor untuk periode 2026-05-01 s.d. 2026-05-31.
- [ ] Menu hanya terlihat bagi pengguna yang mendapat grup reporting.
- [ ] Tanggal awal setelah tanggal akhir ditolak.
- [ ] Company di luar hak pengguna ditolak.
- [ ] Query hanya mengambil jurnal berstatus posted.
- [ ] Query memakai parameter binding.
- [ ] Workbook tetap dapat dibuat ketika periode tidak memiliki data.
- [ ] Sheet detail dapat ditelusuri ke ringkasannya.
