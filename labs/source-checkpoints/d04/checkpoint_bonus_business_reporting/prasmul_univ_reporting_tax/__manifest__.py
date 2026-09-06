{
    "name": "Pelaporan Universitas Prasmul - Operasional Pajak",
    "summary": "Workbook transaksi pajak operasional untuk pelatihan dan peninjauan",
    "description": "Menghasilkan detail, ringkasan, dan pengecekan NPWP dari baris pajak yang sudah diposting.",
    "version": "18.0.1.0.0",
    "category": "Pelaporan",
    "author": "PT Arkana Solusi Digital",
    "website": "https://arkana.co.id",
    "license": "LGPL-3",
    "depends": [
        "account",
        "l10n_id",
        "prasmul_univ_reporting",
    ],
    "external_dependencies": {"python": ["xlsxwriter"]},
    "data": [
        "security/ir.model.access.csv",
        "wizard/tax_report_wizard_views.xml",
    ],
    "installable": True,
}
