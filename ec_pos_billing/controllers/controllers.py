# -*- coding: utf-8 -*-
from odoo import http

# class El-ahorro/facturacionElectronica(http.Controller):
#     @http.route('/el-ahorro/pos_facturacion_electronica/el-ahorro/pos_facturacion_electronica/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/el-ahorro/pos_facturacion_electronica/el-ahorro/pos_facturacion_electronica/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('el-ahorro/pos_facturacion_electronica.listing', {
#             'root': '/el-ahorro/pos_facturacion_electronica/el-ahorro/pos_facturacion_electronica',
#             'objects': http.request.env['el-ahorro/pos_facturacion_electronica.el-ahorro/pos_facturacion_electronica'].search([]),
#         })

#     @http.route('/el-ahorro/pos_facturacion_electronica/el-ahorro/pos_facturacion_electronica/objects/<model("el-ahorro/pos_facturacion_electronica.el-ahorro/pos_facturacion_electronica"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('el-ahorro/pos_facturacion_electronica.object', {
#             'object': obj
#         })