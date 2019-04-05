# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class el-ahorro/ec_11_pos_assigned(models.Model):
#     _name = 'el-ahorro/ec_11_pos_assigned.el-ahorro/ec_11_pos_assigned'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100