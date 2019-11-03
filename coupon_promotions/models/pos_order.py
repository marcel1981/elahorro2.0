from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def create_from_ui(self, orders):
        order_ids = super(PosOrder, self).create_from_ui(orders)
        coupon_obj = self.env["coupon.promotion"]
        for order in order_ids:
            order_data = self.browse(order)
            for row in orders:
                if order_data.pos_reference == row.get("data").get("name"):
                    coupon_obj.search(
                        [
                            (
                                "name",
                                "in",
                                [
                                    pay[2].get("coupon")
                                    for pay in row.get("data").get("statement_ids")
                                    if pay[2].get("coupon")
                                ],
                            )
                        ]
                    ).write(
                        {
                            "used": True,
                            "used_in": self._name,
                            "date_used": fields.Date.context_today(self),
                            "reference": "{},{}".format(self._name, order),
                        }
                    )
        return order_ids
