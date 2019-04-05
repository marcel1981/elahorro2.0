# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ResUsers(models.Model):
    _inherit = ['res.users']

    config_pos = fields.Many2many('pos.config', 'id', string='Puntos de ventas.')
    wise_config = fields.Boolean('Activar users Pos', default=False)


