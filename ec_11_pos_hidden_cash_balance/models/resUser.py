# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ResUsers(models.Model):
    _inherit = ['res.users']
    is_cashier = fields.Boolean("Es cajera", default=False)