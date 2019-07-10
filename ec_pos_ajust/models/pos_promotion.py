from odoo import api, fields, models

class Pos_promotion(models.Model):
    _inherit = 'pos.promotion'

    pos_ids = fields.Many2many('pos.config')