# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class el-ahorro/ec_11_pos_hidden_cash_balance(models.Model):
#     _name = 'el-ahorro/ec_11_pos_hidden_cash_balance.el-ahorro/ec_11_pos_hidden_cash_balance'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100