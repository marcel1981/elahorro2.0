from odoo import api, fields, models

class Pos_promotion(models.Model):
    _inherit = 'pos.promotion'

    pos_id = fields.Many2one('pos.config')