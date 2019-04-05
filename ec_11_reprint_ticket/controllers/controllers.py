# -*- coding: utf-8 -*-
from odoo import http

# class El-ahorro/ecElectronicBilling(http.Controller):
#     @http.route('/el-ahorro/ec_electronic_billing/el-ahorro/ec_electronic_billing/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/el-ahorro/ec_electronic_billing/el-ahorro/ec_electronic_billing/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('el-ahorro/ec_electronic_billing.listing', {
#             'root': '/el-ahorro/ec_electronic_billing/el-ahorro/ec_electronic_billing',
#             'objects': http.request.env['el-ahorro/ec_electronic_billing.el-ahorro/ec_electronic_billing'].search([]),
#         })

#     @http.route('/el-ahorro/ec_electronic_billing/el-ahorro/ec_electronic_billing/objects/<model("el-ahorro/ec_electronic_billing.el-ahorro/ec_electronic_billing"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('el-ahorro/ec_electronic_billing.object', {
#             'object': obj
#         })