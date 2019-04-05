# -*- coding: utf-8 -*-
from odoo import http

# class El-ahorro/ec11PosAssigned(http.Controller):
#     @http.route('/el-ahorro/ec_11_pos_assigned/el-ahorro/ec_11_pos_assigned/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/el-ahorro/ec_11_pos_assigned/el-ahorro/ec_11_pos_assigned/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('el-ahorro/ec_11_pos_assigned.listing', {
#             'root': '/el-ahorro/ec_11_pos_assigned/el-ahorro/ec_11_pos_assigned',
#             'objects': http.request.env['el-ahorro/ec_11_pos_assigned.el-ahorro/ec_11_pos_assigned'].search([]),
#         })

#     @http.route('/el-ahorro/ec_11_pos_assigned/el-ahorro/ec_11_pos_assigned/objects/<model("el-ahorro/ec_11_pos_assigned.el-ahorro/ec_11_pos_assigned"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('el-ahorro/ec_11_pos_assigned.object', {
#             'object': obj
#         })