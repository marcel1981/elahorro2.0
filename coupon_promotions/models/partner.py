#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _get_terms(self):
        return "Test"

    terms = fields.Boolean(_("Accept Terms and Conditions"))
    conditions = fields.Text("Term And Conditions", deafult="_get_terms")

    @api.model
    def create(self, vals):
        today = fields.Date.today()
        coupon_obj = self.env["coupon"]
        promotion_obj = self.env["coupon.promotion"]
        if self.env.context.get("website_id"):
            partner_id = self.search(
                [("identification", "=", vals.get("identification"))]
            )
            if not partner_id:
                partner_id = super(ResPartner, self).create(vals)
            coupon_id = coupon_obj.search(
                [
                    ("date_from", "<=", today),
                    ("date_to", ">=", today),
                    ("state", "=", "confirm"),
                ]
            )
            if coupon_id:
                number = len(coupon_id.mapped("coupon_ids")) + 1
                partner_coupons = promotion_obj.search(
                    [
                        ("partner_id", "=", partner_id.id),
                        ("coupon_id", "=", coupon_id.id),
                    ]
                )
                if len(partner_coupons) < coupon_id.coupon_partner:
                    promotion_obj.create(
                        {
                            "name": "{}-{}-{:0>4}".format(
                                coupon_id.code, partner_id.identification[-4:], number
                            ),
                            "coupon_id": coupon_id.id,
                            "partner_id": partner_id.id,
                            "value": coupon_id.coupon_value,
                        }
                    )
                    promotion_obj.coupon_notify()
            return partner_id
        return super(ResPartner, self).create(vals)
