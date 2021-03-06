#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    coupons = fields.Boolean(
        _("Allow Coupons"), default=False, help=_("Allow payment with coupons!")
    )


class AccountPayment(models.Model):
    _inherit = "account.payment"

    coupon = fields.Boolean(_("Coupon"), related="journal_id.coupons")
    coupon_valid = fields.Boolean(_("Coupon Valid"), default=False)
    coupon_code = fields.Char(_("Coupon Code"))
    coupon_id = fields.Many2one("coupon.promotion", _("Coupon"))

    @api.onchange("coupon_code")
    def _onchange_coupon_code(self):
        promo_obj = self.env["coupon.promotion"]
        today = fields.Date.context_today(self)
        amount = 0
        coupon = False
        valid = False
        for row in self:
            amount = row.amount
            if row.coupon_code:
                if len(row.mapped("invoice_ids").ids) > 1:
                    raise ValidationError(
                        _("You cannot apply the coupon to multiple invoices!")
                    )
                if (
                    row.mapped("invoice_ids")
                    .mapped("payment_ids")
                    .mapped("journal_id")
                    .mapped("coupons")
                ):
                    raise ValidationError(
                        _("You can only register one coupon per invoice!")
                    )
                promo_id = promo_obj.search(
                    [
                        ("name", "=", row.coupon_code),
                        ("partner_id", "=", row.partner_id.id),
                        ("coupon_id.coupon_apply", "in", ["both", "sale"]),
                        ("date_from", "<=", today),
                        ("date_to", ">=", today),
                        ("state", "=", "confirm"),
                    ]
                )
                if not promo_id:
                    raise ValidationError(_("The coupon code entered is incorrect!"))
                if (promo_id.coupon_id.min_amount > 0) and (
                    sum(row.mapped("invoice_ids").mapped("amount_total"))
                    < promo_id.coupon_id.min_amount
                ):
                    raise ValidationError(
                        _(
                            "The coupon only applies to purchases greater than or equal to {}!".format(
                                promo_id.coupon_id.min_amount
                            )
                        )
                    )
                if promo_id.used:
                    raise ValidationError(
                        _("The coupon code entered has already been used!")
                    )
                if (
                    row.mapped("invoice_ids").mapped("team_id").id
                    not in promo_id.mapped("team_ids").ids
                ):
                    raise ValidationError(
                        _(
                            "Coupon code does not apply to the sales channel: {}!".format(
                                ",".join(
                                    map(
                                        str,
                                        row.mapped("invoice_ids")
                                        .mapped("team_id")
                                        .mapped("name"),
                                    )
                                )
                            )
                        )
                    )
                amount = promo_id.value
                coupon = promo_id.id
                valid = True
        return {"value": {"coupon_id": coupon, "coupon_valid": valid, "amount": amount}}

    def action_validate_invoice_payment(self):
        if self.coupon and not self.coupon_valid:
            raise UserError(_("You must enter a valid coupon to continue!"))
        res = super(AccountPayment, self).action_validate_invoice_payment()
        if self.coupon and self.coupon_id:
            self.coupon_id.update(
                {
                    "used": True,
                    "used_in": self.env.context.get("active_model"),
                    "date_used": fields.Date.context_today(self),
                    "reference": "{},{}".format(
                        self.env.context.get("active_model"),
                        self.mapped("invoice_ids").ids[0],
                    ),
                }
            )
        return res
