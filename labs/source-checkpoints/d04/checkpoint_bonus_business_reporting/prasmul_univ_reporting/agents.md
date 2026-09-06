# prasmul_univ_reporting — Fondasi pelaporan bersama

## Tujuan

Menyediakan menu utama `Business Reporting`, grup akses khusus, serta helper
`prasmul.xlsx.report.mixin` untuk format XLSX, validasi filter, dan unduhan file
dari wizard sementara.

## Batas tanggung jawab

Addon ini tidak berisi query accounting atau laporan bisnis tertentu. Kebutuhan
tersebut menjadi tanggung jawab addon seperti `prasmul_univ_reporting_lkps` dan
`prasmul_univ_reporting_tax`.

## Skenario pengujian

- Hanya pengguna dalam `group_business_reporting_user` yang melihat menu utama.
- Rentang tanggal tidak valid dan company tanpa hak akses harus ditolak.
- File hasil dibuat melalui field binary pada transient wizard.

## Istilah untuk pembaca pemula

- `mixin`: model bantuan berisi method bersama, bukan data bisnis baru.
- `TransientModel`: model untuk data sementara seperti filter wizard.
- XLSX: format workbook Excel yang dihasilkan oleh laporan.
- Field binary: tempat menyimpan isi file pada record wizard agar dapat diunduh.
- Hak akses company: pembatas agar pengguna hanya mengambil data perusahaan yang
  memang boleh dibukanya.
