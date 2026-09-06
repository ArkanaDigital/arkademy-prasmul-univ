# prasmul_univ_reporting_lkps — Workbook finansial LKPS parsial

## Alur data

Wizard memvalidasi akses company dan tanggal, lalu ORM mencari ID jurnal posted yang
boleh dibaca berdasarkan record rule. `_get_lkps_data_sql()` hanya mengagregasi ID
tersebut. Python memetakan akun ke kategori rancangan LKPS dan menghasilkan empat
sheet workbook.

## Cakupan

Hanya jurnal posted untuk akun pendapatan, biaya, dan aset tetap yang disertakan.
Mapping kata kunci akun ditampilkan secara transparan dan diberi status
`Perlu Ditinjau` ketika klasifikasinya belum dapat dipercaya. Hasil ini bukan dokumen
pengajuan akreditasi lengkap.

Addon hanya bergantung pada Accounting standar dan core reporting. Distribusi
analitik ditampilkan tanpa klaim bahwa nilainya mewakili program studi.

## Skenario pengujian

- Tolak tanggal terbalik dan company tanpa hak akses.
- Bandingkan jumlah jurnal posted dari ORM dengan cakupan sumber SQL.
- Periksa tanda refund/kredit, akun tanpa mapping, distribusi analitik kosong, dan
  periode tanpa data.

## Istilah untuk pembaca pemula

- ORM: API model Odoo yang digunakan untuk validasi akses dan angka kontrol.
- Raw SQL terparameterisasi: query PostgreSQL dengan nilai filter dikirim terpisah,
  sehingga lebih aman daripada menyusun query melalui penggabungan string.
- Record rule: aturan Odoo yang menentukan record mana yang boleh dilihat pengguna;
  ID sumber diperoleh lewat ORM agar query SQL tidak melewati batas tersebut.
- Mapping: pengelompokan akun accounting ke kategori laporan.
- Coverage: informasi tentang data yang berhasil dicakup dan kekurangannya.
- Rekonsiliasi: membandingkan angka laporan dengan sumbernya.
- Posted: status jurnal yang sudah dikonfirmasi dan masuk pencatatan accounting.
- Perlu Ditinjau: status mapping sementara yang harus dikonfirmasi pengguna bisnis.
- TS, TS-1, dan TS-2: tahun pelaporan LKPS terakhir serta satu dan dua tahun
  sebelumnya; contoh ini masih memakai periode tanggal aktual.
- Distribusi analitik: pembagian biaya atau pendapatan ke dimensi seperti unit atau
  cost center; nilainya belum tentu merupakan program studi.
