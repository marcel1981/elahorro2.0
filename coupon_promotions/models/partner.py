#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    coupon_count = fields.Integer(
        compute="_compute_coupon_count", string=_("# of Coupons")
    )
    coupon_ids = fields.One2many("coupon.promotion", "partner_id", _("Coupons"))

    def _compute_coupon_count(self):
        all_partners = self.search([("id", "child_of", self.ids)])
        all_partners.read(["parent_id"])

        coupon_groups = self.env["coupon.promotion"].read_group(
            domain=[("partner_id", "in", all_partners.ids)],
            fields=["partner_id"],
            groupby=["partner_id"],
        )
        for group in coupon_groups:
            partner = self.browse(group["partner_id"][0])
            while partner:
                if partner in self:
                    partner.coupon_count += group["partner_id_count"]
                partner = partner.parent_id

    @api.multi
    def partner_coupons(self):
        tree = self.env.ref("coupon_promotions.view_coupon_promotion_tree", False)
        return {
            "name": _("Coupons {}".format(self.name)),
            "type": "ir.actions.act_window",
            "res_model": "coupon.promotion",
            "view_mode": "tree",
            "views": [(tree.id, "tree")],
            "domain": [("partner_id", "in", self.ids)],
            "res_id": False,
            "target": "current",
        }
