#!/usr/bin/env python
# -*- coding: utf-8 -*-
import base64
from io import BytesIO

from barcode import generate
from barcode.writer import ImageWriter
from jinja2 import Template
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Coupon(models.Model):
    _name = "coupon"

    name = fields.Char(_("Name"))
    code = fields.Char(_("Code"), size=4)
    team_id = fields.Many2one("crm.team", _("Sales Team"))
    date_from = fields.Date(_("From"))
    date_to = fields.Date(_("To"))
    coupon_number = fields.Integer(_("Coupons Available"))
    coupon_left = fields.Integer(
        _("Coupons Left"), compute="_get_delivered_coupons", store=True
    )
    coupon_partner = fields.Integer(_("Number of Coupons per Customer"))
    coupon_value = fields.Monetary(_("Coupon Amount"))
    coupon_apply = fields.Selection(
        [("both", _("Both")), ("sale", _("Sale Orders")), ("pos", _("Point of Sale"))],
        _("Coupon Apply"),
        default="both",
    )
    coupon_ids = fields.One2many("coupon.promotion", "coupon_id", "Coupons")
    currency_id = fields.Many2one(
        "res.currency", default=lambda x: x.env.user.company_id.currency_id.id
    )
    body_html = fields.Text("Mail Template")
    state = fields.Selection(
        [("draft", _("Draft")), ("confirm", _("Confirm")), ("cancel", _("Cancel"))],
        string=_("State"),
        default="draft",
    )

    @api.multi
    @api.depends("coupon_number", "coupon_ids")
    def _get_delivered_coupons(self):
        for row in self:
            row.coupon_left = row.coupon_number - len(row.mapped("coupon_ids").ids)
        return True

    @api.constrains("code")
    def _check_code(self):
        for row in self:
            if len(row.code) < 4:
                raise ValidationError(
                    _("The length of the promotion code must be 4 characters!")
                )


class CouponPromotion(models.Model):
    _name = "coupon.promotion"

    name = fields.Char(_("Code"))
    barcode = fields.Binary(_("Barcode"), compute="_get_barcode")
    partner_id = fields.Many2one("res.partner", _("Customer"))
    coupon_id = fields.Many2one("coupon", _("Coupon"))
    send = fields.Boolean("Email Send", default=False)
    currency_id = fields.Many2one(
        "res.currency", related="coupon_id.currency_id", store=True
    )
    value = fields.Monetary(_("Amount"))
    used = fields.Boolean(_("Used"))
    used_in = fields.Char(_("Used in"))

    @api.multi
    def _get_barcode(self):
        for row in self:
            if ImageWriter is not None:
                ean = BytesIO()
                generate(
                    "code128", u"{}".format(row.name), writer=ImageWriter(), output=ean
                )
                ean.seek(0)
                jpgdata = ean.read()
                imgdata = base64.encodestring(jpgdata)
                row.barcode = imgdata
        return True

    @api.model
    def coupon_notify(self):
        data = {}
        # coupon_ids = self.search([("send", "=", False)])
        coupon_ids = self.search([])
        for row in coupon_ids:
            mail_obj = self.env["mail.mail"]
            variables = {
                "name": row.coupon_id.name,
                "code": row.name,
                "barcode": '<img src="data:image/png;base64,{}"/>'.format(row.barcode),
            }
            template = Template(
                row.coupon_id.body_html,
                trim_blocks=True,
                lstrip_blocks=True,
                autoescape=True,
            )
            vals = {
                "state": "outgoing",
                "subject": _(
                    "{}: {}".format(
                        self.env.user.company_id.name_get()[0][1], row.coupon_id.name
                    )
                ),
                "body_html": template.render(variables),
                "email_to": row.partner_id.email,
                "email_from": row.env.user.company_id.email,
            }
            mail_obj.create(vals)
            row.send = True
        return True
