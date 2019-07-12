from odoo import api, fields, models

class Pos_promotion(models.Model):
    _inherit = 'pos.promotion'

    pos_ids = fields.Many2many('pos.config')
    promotion_type = fields.Selection(
        [
            ('buy_x_get_y','Buy X Get Y Free'),
            ('buy_x_get_dis_y','Buy X Get Discount On Y'),
            ('buy_x_get_coupon','X total amount Y coupon'),
            ('quantity_discount','Percent Discount on Quantity'),
            ('quantity_price','Fix Discount on Quantity'),
            ('discount_on_multi_product','Discount On Combination Products'),
            ('discount_on_multi_categ','Discount On Multiple Categories'),
            ('discount_on_above_price','Discount On Above Price')
        ], default="buy_x_get_y",require=True
    )