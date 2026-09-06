# prasmul_univ_reporting_tax — Workbook operasional pajak

## Alur data

Wizard memvalidasi akses company dan tanggal, lalu ORM mencari ID jurnal posted yang
boleh dibaca berdasarkan record rule. Method `_get_tax_data_sql()` yang
terparameterisasi hanya membaca baris pajak dari ID tersebut. Sheet workbook
mencakup transaksi sumber, pengecualian NPWP kosong, ringkasan pajak, dan kontrol.

## Batas tanggung jawab

Ini merupakan laporan operasional, bukan pelaporan pajak resmi atau pengganti
Coretax/e-Faktur. Nilai debit, kredit, saldo, dan absolut tetap ditampilkan agar
pengguna dapat mengenali refund dan reversal tanpa bergantung pada total yang
menyesatkan.

## Skenario pengujian

- Tolak tanggal terbalik dan company tanpa hak akses.
- Periksa fallback tanggal invoice, NPWP kosong, refund, dan periode tanpa data.
- Rekonsiliasi jumlah baris SQL dan total kelompok dengan sheet detail.

## Istilah untuk pembaca pemula

- Baris pajak: journal item yang menunjuk master pajak melalui `tax_line_id`.
- Record rule: aturan Odoo yang membatasi record yang boleh dibaca pengguna; ID
  jurnal diambil lewat ORM agar query SQL tidak melewati aturan ini.
- NPWP: identitas pajak partner yang disimpan pada field `vat`.
- Coretax/e-Faktur: sistem resmi perpajakan; workbook ini hanya membantu pengecekan
  internal dan tidak menggantikan sistem tersebut.
- Saldo bersih: nilai debit dikurangi kredit.
- Nominal absolut: nilai tanpa tanda negatif; dipakai untuk melihat volume transaksi.
- Refund: koreksi/pengembalian invoice; reversal: jurnal pembalik transaksi.
- Rekonsiliasi: mencocokkan ringkasan dengan baris detail agar total dapat ditelusuri.
