# Day 4 Supplement — Membaca Real Case QWeb PDF Prasmul

## Tujuan

Materi tambahan ini dipakai setelah hands-on lab Day 4 selesai. Peserta
membedah report QWeb PDF yang sudah dipakai di Prasmul untuk menghubungkan
konsep lab dengan kode production.

Peserta tidak perlu mengimplementasikan ulang report-report ini pada latihan
pertama. Fokusnya adalah mengenali pola, dependency data, dan sumber
kompleksitasnya.

## Urutan Pembahasan

1. Lab report sertifikat `academy.enrollment` sebagai baseline.
2. Kwitansi Prasmul sebagai real case paling sederhana.
3. Invoice Prasmul sebagai contoh relasi dan format data akuntansi.
4. Payment Proposal sebagai contoh loop, agregasi, pagination, dan approval.
5. Purchase Order sebagai contoh report production yang kompleks.

## Peta Tingkat Kesulitan

| Report | Tingkat | Konsep utama |
|---|---|---|
| Kwitansi | Mudah | `t-out`, `t-field`, monetary, layout |
| Invoice | Sedang | invoice lines, bank, signature, `num2words` |
| Payment Proposal | Sedang-sulit | pagination, agregasi, relasi bill, approval |
| Purchase Order | Sulit | multi-file template, CSS, JavaScript, pagination, config |

## Report yang Dibaca

### 1. Kwitansi

Source: `prasmul_univ_account/reports/kwitansi_prasmul_univ.xml`

Perhatikan:

- `web.basic_layout`
- field payment seperti `partner_id`, `amount`, `memo`, dan `date`
- widget monetary
- helper `num2words`
- conditional image logo

### 2. Invoice

Source: `prasmul_univ_account/reports/invoice_prasmul_univ.xml`

Perhatikan:

- loop `invoice_line_ids`
- format currency pada harga dan subtotal
- data tambahan dari `partner_bank_id`
- signature melalui `sig1_id`
- perbedaan `t-out` dan `t-field`

### 3. Payment Proposal

Source: `prasmul_univ_account/reports/payment_proposal.xml`

Perhatikan:

- data berasal dari `o.payment_ids`
- pagination dengan `range()` dan slicing recordset
- total dengan `sum()`
- data bill melalui `reconciled_bill_ids`
- signature dan status review

### 4. Purchase Order

Source: `prasmul_univ_purchase/report/purchase_order_report_action.xml`

Template ini dibantu beberapa file lain di folder `report/templates/`.
Perhatikan:

- pemisahan template, style, script, dan page section
- pagination manual berdasarkan jumlah line
- kalkulasi diskon, pajak, dan total
- data purchase request terkait
- signature dari `ir.config_parameter`
- custom helper seperti `format_indo_amount()`

## Checklist Analisis

Untuk setiap report, jawab pertanyaan berikut:

- Model apa yang menjadi sumber report?
- Apa external ID dari `ir.actions.report`?
- Template utama memanggil layout apa?
- Recordset dan field apa yang digunakan?
- Apakah ada method Python custom yang dipanggil dari QWeb?
- Apa yang terjadi jika field atau relasi datanya kosong?
- Bagian mana yang bisa dibuat lebih sederhana untuk kebutuhan training?

## Catatan untuk Trainer

Gunakan record development yang sudah diverifikasi memiliki data detail.
Jangan mencetak record hanya berdasarkan keberadaan ID. Validasi juga
`exists()`, relasi line/payment, partner, company, dan field yang memang
dibaca oleh template.
