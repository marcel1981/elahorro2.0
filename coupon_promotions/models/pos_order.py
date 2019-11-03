from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def create_from_ui(self, orders):
        order_ids = super(PosOrder, self).create_from_ui(orders)
        self.env["coupon.promotion"].search(
            [
                (
                    "name",
                    "in",
                    [
                        j[2].get("coupon")
                        for i in orders
                        for j in i["data"]["statement_ids"]
                        if j[2].get("coupon")
                    ],
                )
            ]
        ).write(
            {
                "used": True,
                "used_in": self._name,
                "date_used": fields.Date.context_today(self),
                "reference": "{},{}".format(self._name, self.id),
            }
        )
        return order_ids
