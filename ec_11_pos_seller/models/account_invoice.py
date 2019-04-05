# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    pos_location_id = fields.Many2one(
        "pos.location",
        string="Ubicacion"
    )
    pos_salesman_id = fields.Many2one(
        "pos.salesman",
        string="Vendedora de Mostrador")


