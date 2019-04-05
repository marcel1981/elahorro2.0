# -*- coding: utf-8 -*-
import os
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64

logger = logging.getLogger(__name__)


class Establishment(models.Model):
    _name = 'company.establishment'

    @api.multi
    def _get_company(self):
        return self.env.user.company_id.id

    number_establish = fields.Char(string="Número de establecimiento", required=True, size=3)
    address_store = fields.Text(string="Dirección del almacén", required=True)
    company = fields.Many2one('res.company', 'Compañia a la que aplica', default=_get_company, required=True)

    @api.constrains('number_establish')
    def _check_number_establish(self):
        for record in self:
            if not record.number_establish.isdigit():
                raise ValidationError("Número de establecimiento debe ser solo números: %s" % record.number_establish)

    @api.multi
    def name_get(self):
        data = []
        for establishment in self:
            display_value = '({}) {}'.format(establishment.number_establish,
                                               establishment.address_store)
            data.append((establishment.id, display_value))
        return data


