# -*- coding: utf-8 -*-
import os
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

logger = logging.getLogger(__name__)


class PointEmission(models.Model):
    _name = 'invoice.point.emission'

    @api.multi
    def _get_company(self):
        return self.env.user.company_id.id

    number_establishment = fields.Many2one('company.establishment', 'Número de establecimiento RUC')
    address = fields.Text(string='Adress', related='number_establishment.address_store', readonly=True,)
    code_emission = fields.Char(string="Código punto de emisión", size=3, default="001")
    point_of_sale = fields.Many2one('pos.config', 'Punto de venta al que aplica')
    type_emision = fields.Char(string="Tipo emisión", size=1, default='1')
    current_number_invoice = fields.Integer(string="Sequencia facturas")
    current_credit_note = fields.Integer(string="Sequencia notas de credito")
    currentRetention = fields.Integer(string="Sequencia notas de Retenciones")
    is_retention = fields.Boolean("Retención por defecto", default=False)


    @api.constrains('code_emission')
    def _check_code_emission(self):
        for record in self:
            if not record.code_emission.isdigit():
                raise ValidationError("Código punto de emisión debe ser solo números: %s" % record.code_emission)

    @api.multi
    def name_get(self):
        data = []
        for emission in self:
            display_value = '{}({})'.format(emission.code_emission, emission.number_establishment.address_store)
            data.append((emission.id, display_value))
        return data

