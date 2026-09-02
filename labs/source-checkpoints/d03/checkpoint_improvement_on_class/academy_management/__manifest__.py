# -*- coding: utf-8 -*-
{
    'name': "Academy Management",

    'summary': "Dibangun untuk managemen akademi",

    'description': """
* Master Data
* Pendaftaran Siswa
    """,

    'author': "Arkana",
    'website': "https://www.arkana.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '18.0.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/academy_groups.xml',
        'security/academy_record_rules.xml',
        'data/academy_data.xml',
        'views/academy_course_views.xml',
        'views/academy_student_views.xml',
        'views/academy_batch_views.xml',
        'views/academy_enrollment_views.xml',
        'views/academy_course_inherit_views.xml',
        'views/academy_menu_views.xml',
        # 'views/views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

