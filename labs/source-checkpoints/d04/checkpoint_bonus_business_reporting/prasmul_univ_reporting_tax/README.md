# Laporan Operasional Pajak

Menghasilkan workbook dengan sheet `database`, `cek npwp`, `summary`, dan `Kontrol`
dari baris pajak Odoo yang sudah diposting.

Hasilnya ditujukan untuk peninjauan operasional dan pelatihan. Laporan ini tidak
menggantikan Coretax, e-Faktur, bukti potong, atau SPT resmi.

## Cara kerja singkat

1. Pengguna memilih company serta tanggal awal dan akhir pada wizard.
2. ORM mencari ID jurnal yang boleh dibaca pengguna sesuai record rule.
3. Raw SQL mengambil baris pajak hanya dari ID jurnal hasil pencarian ORM tersebut.
4. Python mengelompokkan data per jenis pajak dan memisahkan transaksi dengan NPWP
   kosong.
5. Workbook dikirim kembali melalui field binary pada wizard.

## Isi workbook

- `database`: rincian baris pajak yang menjadi sumber laporan.
- `cek npwp`: transaksi dengan NPWP partner yang masih kosong.
- `summary`: jumlah baris, debit, kredit, saldo bersih, dan nominal absolut per
  jenis pajak.
- `Kontrol`: informasi dasar untuk memeriksa periode dan jumlah data.

## Istilah penting

- **NPWP** adalah nomor identitas wajib pajak yang dibaca dari field `vat` partner
  Odoo.
- **Baris pajak** adalah journal item yang mempunyai `tax_line_id`. Baris dasar
  invoice yang hanya memiliki `tax_ids` tidak dihitung sebagai baris pajak.
- **Penggunaan pajak** adalah kode Odoo yang menunjukkan apakah master pajak
  dipakai untuk transaksi penjualan atau pembelian.
- **Record rule** adalah aturan yang membatasi record Odoo untuk seorang pengguna.
  ID jurnal dibaca melalui ORM sebelum query SQL dijalankan agar batas ini dijaga.
- **Tanggal laporan** memakai tanggal invoice jika tersedia. Untuk jurnal tanpa
  tanggal invoice, sistem memakai tanggal jurnal.
- **Debit dan kredit** ditampilkan terpisah agar arah pencatatan tetap terlihat.
- **Saldo bersih** adalah debit dikurangi kredit pada baris pajak.
- **Nominal absolut** menghilangkan tanda positif atau negatif. Nilai ini berguna
  untuk melihat volume, tetapi tidak boleh dipakai sendirian sebagai pajak terutang.
- **Refund** adalah dokumen pengembalian atau koreksi invoice.
- **Reversal** adalah jurnal pembalik. Transaksi ini dapat mengurangi atau membalik
  nilai transaksi sebelumnya.
- **Laporan operasional** membantu pengecekan internal, sedangkan **pelaporan resmi**
  harus mengikuti aturan dan aplikasi perpajakan yang berlaku.
