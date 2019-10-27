# -*- coding: utf-8 -*-
from odoo import http

# class EcPosAjust(http.Controller):
#     @http.route('/ec_pos_ajust/ec_pos_ajust/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ec_pos_ajust/ec_pos_ajust/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ec_pos_ajust.listing', {
#             'root': '/ec_pos_ajust/ec_pos_ajust',
#             'objects': http.request.env['ec_pos_ajust.ec_pos_ajust'].search([]),
#         })

#     @http.route('/ec_pos_ajust/ec_pos_ajust/objects/<model("ec_pos_ajust.ec_pos_ajust"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ec_pos_ajust.object', {
#             'object': obj
#         })