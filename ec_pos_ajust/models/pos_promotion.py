from odoo import api, fields, models
from odoo.exceptions import UserError


class PosPromotion(models.Model):
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
    value_per_coupon = fields.Float('Valor por cupon')
    name_raffle = fields.Char('Nombre del Sorteo')
    date_raffle = fields.Date('Fecha del Sorteo')
    description = fields.Char('Descripción')

    @api.multi
    def view_coupons(self):
        return {
            'name': 'Cupones',
            'view_mode': 'tree',
            # 'view_id': self.env.ref('ec_pos_ajust.action_promotion_tree').id,
            'res_model': 'pos.promotion.history',
            'domain': "[('promotion_id', 'in',{})]".format(self.ids),
            'type': 'ir.actions.act_window'
        }

    @api.constrains('promotion_code')
    def _check_promotion_code(self):
        if self.search_count([
                ('promotion_code', '=', self.promotion_code)
        ]) > 1:
            raise UserError(
                "No pueden existir dos promoción con el mismo Código"
            )


class PosPromotionHistory(models.Model):
    _name = 'pos.promotion.history'

    promotion_id = fields.Many2one('pos.promotion')
    partner_id = fields.Many2one('res.partner', string='Cliente')
    seq = fields.Char('Numero de cupon')
    date = fields.Datetime('Fecha')
    identification = fields.Char(related='partner_id.identification')