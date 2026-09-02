# -*- coding: utf-8 -*-
# from odoo import http


# class AcademyManagement(http.Controller):
#     @http.route('/academy_management/academy_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/academy_management/academy_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('academy_management.listing', {
#             'root': '/academy_management/academy_management',
#             'objects': http.request.env['academy_management.academy_management'].search([]),
#         })

#     @http.route('/academy_management/academy_management/objects/<model("academy_management.academy_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('academy_management.object', {
#             'object': obj
#         })

