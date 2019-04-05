# -*- coding: utf-8 -*-
from odoo import http

# class El-ahorro/ec11PosHiddenCashBalance(http.Controller):
#     @http.route('/el-ahorro/ec_11_pos_hidden_cash_balance/el-ahorro/ec_11_pos_hidden_cash_balance/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/el-ahorro/ec_11_pos_hidden_cash_balance/el-ahorro/ec_11_pos_hidden_cash_balance/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('el-ahorro/ec_11_pos_hidden_cash_balance.listing', {
#             'root': '/el-ahorro/ec_11_pos_hidden_cash_balance/el-ahorro/ec_11_pos_hidden_cash_balance',
#             'objects': http.request.env['el-ahorro/ec_11_pos_hidden_cash_balance.el-ahorro/ec_11_pos_hidden_cash_balance'].search([]),
#         })

#     @http.route('/el-ahorro/ec_11_pos_hidden_cash_balance/el-ahorro/ec_11_pos_hidden_cash_balance/objects/<model("el-ahorro/ec_11_pos_hidden_cash_balance.el-ahorro/ec_11_pos_hidden_cash_balance"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('el-ahorro/ec_11_pos_hidden_cash_balance.object', {
#             'object': obj
#         })