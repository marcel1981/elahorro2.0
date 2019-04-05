# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosLocation(models.Model):
    _name = "pos.location"

    name = fields.Char("Nombre")
    active = fields.Boolean("Active", default=True)
