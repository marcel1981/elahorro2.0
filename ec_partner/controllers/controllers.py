# -*- coding: utf-8 -*-
from odoo import http

# class El-ahorro/ecPartner(http.Controller):
#     @http.route('/el-ahorro/ec_partner/el-ahorro/ec_partner/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/el-ahorro/ec_partner/el-ahorro/ec_partner/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('el-ahorro/ec_partner.listing', {
#             'root': '/el-ahorro/ec_partner/el-ahorro/ec_partner',
#             'objects': http.request.env['el-ahorro/ec_partner.el-ahorro/ec_partner'].search([]),
#         })

#     @http.route('/el-ahorro/ec_partner/el-ahorro/ec_partner/objects/<model("el-ahorro/ec_partner.el-ahorro/ec_partner"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('el-ahorro/ec_partner.object', {
#             'object': obj
#         })