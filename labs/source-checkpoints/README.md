# Source Checkpoints — `academy_management`

Snapshot kode modul di setiap titik lab. Gunanya **satu**: peserta yang tertinggal atau kodenya rusak bisa langsung menyusul tanpa menunggu kelas.

## Isi

| Hari | Checkpoint |
|---|---|
| **d01** | `a_module_only` → `b_models_ready` → `c_final` |
| **d02** | `a_custom_views` → `b_relations` → `c_inheritance` → `d_computed_onchange` → `final_day2` |
| **d03** | `a_constraints` → `b_state_approval` → `c_approval_monitoring_views` → `d_security_for_approval` → `e_wizard` → `final_day3` |
| **d04** | `a_pdf_report` → `b_report_inheritance` → `c_excel_export` → `d_rest_api_consumer` → `e_external_api` → `final_day4` |
| **d05** | `a_controller_basics` → `b_get_courses` → `c_get_course_detail` → `d_post_enrollment_request` → `e_api_key_boundary` → `final_day5` |

Tiap folder berisi satu modul `academy_management/` yang utuh dan bisa langsung di-install.

## Cara Pakai

### Menyusul ketinggalan

```bash
# dari folder development/
rm -rf custom-addons/academy_management
cp -R materi/labs/source-checkpoints/d02/checkpoint_b_relations/academy_management \
      custom-addons/

./odoo/odoo-bin -c odoo.conf -d academy -u academy_management
```

Lanjutkan lab dari step berikutnya.

### Membandingkan dengan kode sendiri

```bash
diff -ru custom-addons/academy_management \
         materi/labs/source-checkpoints/d02/checkpoint_b_relations/academy_management
```

Cara tercepat menemukan apa yang terlewat saat kode Anda error tapi tidak tahu di mana.

### Mulai hari baru dari kondisi bersih

Awal Day 3, pakai `d02/checkpoint_final_day2` supaya semua peserta berangkat dari titik yang sama.

## Aturan Main

- **Checkpoint adalah jaring pengaman, bukan jalan pintas.** Ketik sendiri dulu. Menyalin tanpa mengetik membuat Anda lulus lab tapi tidak bisa apa-apa saat kerja nyata.
- **Selalu `-u` setelah menyalin.** Kode di disk berubah, tapi database belum tahu.
- **Database tidak ikut ter-reset.** Kalau data lama bikin constraint gagal, bersihkan datanya atau pakai database baru.

## Catatan Versi — Sudah Dikonversi ke Odoo 18

Checkpoint ini aslinya ditulis untuk Odoo 19. Dua API tidak ada di Odoo 18 dan sudah dikonversi:

| Odoo 19 (asli) | Odoo 18 (dipakai di sini) | File terdampak |
|---|---|---|
| `_check_x = models.Constraint(sql, msg)` | `_sql_constraints = [(nama, sql, msg)]` | 2 model di `d05/checkpoint_final_day5` |
| `res.groups.privilege` + `privilege_id` | `ir.module.category` + `category_id` | 18 file `security/academy_groups.xml` |

Versi di semua `__manifest__.py` juga sudah diubah dari `19.0.x` menjadi `18.0.x`.

> Kalau menemukan contoh kode Odoo 19 di internet dengan pola di kolom kiri, itu **tidak akan jalan** di Odoo 18. Ini contoh nyata kenapa versi addon harus dicek, bukan diasumsikan — dibahas di materi Day 1.

## Status Verifikasi

| Cek | Hasil |
|---|---|
| Syntax Python (274 file) | Lolos |
| XML well-formed (290 file) | Lolos |
| Konsistensi kolom CSV (24 file) | Lolos |
| **Install & jalan di Odoo 18** | **Belum diuji** |

> Pemeriksaan di atas hanya membuktikan file-nya tidak rusak secara sintaks — **bukan** bahwa modulnya berhasil di-install dan berfungsi di Odoo 18. Trainer wajib menjalankan install bersih tiap checkpoint sebelum training dimulai:
>
> ```bash
> createdb academy_test
> ./odoo/odoo-bin -c odoo.conf -d academy_test -i academy_management --stop-after-init
> ```
