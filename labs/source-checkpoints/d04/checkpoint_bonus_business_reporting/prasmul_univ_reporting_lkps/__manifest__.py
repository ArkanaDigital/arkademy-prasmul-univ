{
    "name": "Pelaporan Universitas Prasmul - LKPS Parsial",
    "summary": "Workbook finansial LKPS parsial untuk pelatihan dan persiapan data",
    "description": "Menghasilkan workbook finansial LKPS parsial dari jurnal accounting yang sudah diposting.",
    "version": "18.0.1.0.0",
    "category": "Pelaporan",
    "author": "PT Arkana Solusi Digital",
    "website": "https://arkana.co.id",
    "license": "LGPL-3",
    "depends": [
        "account",
        "prasmul_univ_reporting",
    ],
    "external_dependencies": {"python": ["xlsxwriter"]},
    "data": [
        "security/ir.model.access.csv",
        "wizard/lkps_report_wizard_views.xml",
    ],
    "installable": True,
}
