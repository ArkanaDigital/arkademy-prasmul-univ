{
    "name": "Pelaporan Universitas Prasmul",
    "summary": "Menu, keamanan, dan bantuan XLSX bersama untuk laporan bisnis",
    "description": "Fondasi bersama untuk pengembangan laporan bisnis pada project pelatihan Prasmul.",
    "version": "18.0.1.0.0",
    "category": "Pelaporan",
    "author": "PT Arkana Solusi Digital",
    "website": "https://arkana.co.id",
    "license": "LGPL-3",
    "depends": ["base"],
    "external_dependencies": {"python": ["xlsxwriter"]},
    "data": [
        "security/reporting_security.xml",
        "views/reporting_menu.xml",
    ],
    "application": True,
    "installable": True,
}
