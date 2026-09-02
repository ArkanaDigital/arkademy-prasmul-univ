# Checkpoint Day 3 — Improvement on Class

Snapshot source dari hasil coding workspace pada 2 September 2026.

Checkpoint ini dibuat terpisah dari checkpoint_final_day3 agar baseline resmi
lab tetap tidak berubah. Isinya mempertahankan improvement implementasi kelas,
terutama:

- default course dan generator batch code;
- domain course berdasarkan level;
- default capacity dan onchange end date;
- related field Batch pada Enrollment;
- validasi kapasitas saat enrollment confirmed;
- audit field dan chatter pada workflow enrollment;
- security group, access rights, dan record rules yang sudah dikerjakan.

Status: snapshot hasil coding, belum menggantikan checkpoint resmi dan belum
menandakan seluruh checklist Day 3 sudah selesai. Gunakan lab-d03.md untuk
daftar gap, Q&A, dan pekerjaan lanjutan.

## Cara membandingkan

    diff -ru custom-addons/academy_management \
      materi/labs/source-checkpoints/d03/checkpoint_improvement_on_class/academy_management

Source ini tidak menyertakan __pycache__ atau file .pyc.
