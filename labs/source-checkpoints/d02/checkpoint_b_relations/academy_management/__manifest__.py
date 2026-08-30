{
    'name': 'Academy Management',
    'version': '18.0.2.0.0',
    'category': 'Education',
    'summary': 'Academy Management System - Day 2 (Data Terhubung)',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/academy_data.xml',
        'views/academy_course_views.xml',
        'views/academy_student_views.xml',
        'views/academy_batch_views.xml',
        'views/academy_enrollment_views.xml',
        'views/academy_views.xml',
        'views/academy_menus.xml',
    ],
    'application': True,
    'license': 'LGPL-3',
}
