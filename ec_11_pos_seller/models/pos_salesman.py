# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosSalesman(models.Model):
    _name = "pos.salesman"

    name = fields.Char("Nombre")
    identification = fields.Char("Identificacion", copy=False)
    active = fields.Boolean("Active", default=True)
    barcode = fields.Char(
        string="Barcode",
        copy=False,
        help="Inserte un Codigo de Barras Vendedor estilo 47777777xxxx")
    location = fields.Many2one("pos.location", string="Ubicacion/Almacen")

    _sql_constraints = [
        ('identification unique',
         'unique(identification)',
         "Identificacion vendedor ya existente"),
        ('Barcode POS Salesman unique',
         'unique(barcode)',
         "Codigo Barras vendedor ya existente"),
    ]
