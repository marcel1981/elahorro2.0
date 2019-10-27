#!/usr/bin/env python
# -*- coding: utf-8 -*-
import base64
from io import BytesIO

from barcode import generate
from barcode.writer import ImageWriter
from jinja2 import Template
from lxml import etree
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Coupon(models.Model):
    _name = "coupon"

    name = fields.Char(
        _("Name"), readonly=True, states={"draft": [("readonly", False)]}
    )
    code = fields.Char(
        _("Code"), size=4, readonly=True, states={"draft": [("readonly", False)]}
    )
    date_from = fields.Date(
        _("From"), readonly=True, states={"draft": [("readonly", False)]}
    )
    date_to = fields.Date(
        _("To"), readonly=True, states={"draft": [("readonly", False)]}
    )
    coupon_number = fields.Integer(
        _("Coupons Available"), readonly=True, states={"draft": [("readonly", False)]}
    )
    coupon_left = fields.Integer(
        _("Coupons Left"), compute="_get_delivered_coupons", store=True
    )
    coupon_partner = fields.Integer(
        _("Number of Coupons per Customer"),
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    coupon_value = fields.Monetary(
        _("Coupon Amount"), readonly=True, states={"draft": [("readonly", False)]}
    )
    coupon_apply = fields.Selection(
        [("both", _("Both")), ("sale", _("Sale Orders")), ("pos", _("Point of Sale"))],
        _("Coupon Apply"),
        default="both",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    coupon_ids = fields.One2many("coupon.promotion", "coupon_id", "Coupons")
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda x: x.env.user.company_id.currency_id.id,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    body_html = fields.Text(
        "Mail Template", readonly=True, states={"draft": [("readonly", False)]}
    )
    team_ids = fields.Many2many(
        "crm.team",
        "coupon_crm_team_rel",
        "coupon_id",
        "team_id",
        _("Sale Chanels"),
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    min_amount = fields.Monetary(
        _("Minimum Purchase"), readonly=True, states={"draft": [("readonly", False)]}
    )
    state = fields.Selection(
        [("draft", _("Draft")), ("confirm", _("Confirm")), ("cancel", _("Cancel"))],
        string=_("State"),
        default="draft",
    )

    @api.multi
    def confirm(self):
        for row in self:
            row.state = "confirm"
        return True

    @api.multi
    def cancel(self):
        for row in self:
            row.state = "cancel"
        return True

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

    @api.multi
    @api.depends("name")
    def _get_number(self):
        for row in self:
            number = ""
            if row.name:
                number = row.name.split("-")[-1:][0]
            row.number = number
        return True

    name = fields.Char(_("Code"))
    number = fields.Char(_("Number"), compute="_get_number", store=True)
    partner_id = fields.Many2one("res.partner", _("Customer"))
    identification = fields.Char(
        "Identification", related="partner_id.identification", store=True
    )
    coupon_id = fields.Many2one("coupon", _("Coupon"))
    send = fields.Boolean("Email Send", default=False)
    currency_id = fields.Many2one(
        "res.currency", related="coupon_id.currency_id", store=True
    )
    date_from = fields.Date(_("From"), related="coupon_id.date_from", store=True)
    date_to = fields.Date(_("To"), related="coupon_id.date_to", store=True)
    date_used = fields.Date(_("Date Used"))
    team_ids = fields.Many2many(
        "crm.team",
        "coupon_promotion_crm_team_rel",
        "coupon_id",
        "team_id",
        _("Sale Chanels"),
        related="coupon_id.team_ids",
        store=True,
    )
    value = fields.Monetary(_("Amount"))
    used = fields.Boolean(_("Used"))
    used_in = fields.Char(_("Used in"))
    state = fields.Selection(
        [("draft", _("Draft")), ("confirm", _("Confirm")), ("cancel", _("Cancel"))],
        string=_("State"),
        default="draft",
        related="coupon_id.state",
        store=True,
    )

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        res = models.Model.fields_view_get(
            self, view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        update = view_type in ["form", "tree"]
        if update:
            doc = etree.XML(res["arch"])
            for t in doc.xpath("//" + view_type):
                t.attrib["create"] = "false"
                t.attrib["edit"] = "false"
            res["arch"] = etree.tostring(doc)
        return res

    @api.model
    def coupon_notify(self):
        data = {}
        coupon_ids = self.search([("send", "=", False)])
        for row in coupon_ids:
            mail_obj = self.env["mail.mail"]
            ean = BytesIO()
            generate(
                "code128", u"{}".format(row.name), writer=ImageWriter(), output=ean
            )
            ean.seek(0)
            jpgdata = ean.read()
            imgdata = base64.encodestring(jpgdata)
            variables = {
                "name": row.coupon_id.name,
                "partner": row.partner_id.name_get()[0][1],
                "date_to": row.coupon_id.date_to,
                "code": row.name,
                "barcode": '<img src="data:image/jpeg;base64,{}" />'.format(
                    imgdata.decode("utf-8")
                ),
                "amount": row.value,
                "min_amount": row.coupon_id.min_amount,
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
                "body_html": template.render(**variables),
                "email_to": row.partner_id.email,
                "email_from": row.env.user.company_id.email,
                "author_id": row.env.user.company_id.partner_id.id,
            }
            mail_obj.create(vals)
            row.send = True
        return True
