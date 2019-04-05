# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = 'account.tax'
    codeSRI = fields.Char(string="Código impuesto SRI", size=5)
    typeRetention = fields.Selection([('1', 'Impuesto Retencion sobre la Renta'),
                                      ('2', 'Impuesto Retencion sobre el IVA')],
                                     string='Typo de Retención')


class AccountRetentionTax(models.Model):
    _name = 'account.retention.tax'



    @api.one
    def calculateAmountBase(self):
        if self.typeRetention == '1':
            amount = self.tax_id.amountUntaxed
        elif self.typeRetention == '2':
            amount = self.tax_id.amountTax
        self.baseAmount = self.tax_id.amountTax

    tax_id = fields.Many2one('invoice.retention', string='Impuestos Retenciones')
    tax = fields.Many2one('account.tax', 'Detalle de Impuestos', copy=False)
    typeRetention = fields.Selection([('1', 'Impuesto Retencion sobre la Renta'),
                                      ('2', 'Impuesto Retencion sobre el IVA')],
                                      string='Typo de Retención',
                                      related='tax.typeRetention',
                                      readonly=True,)
    account = fields.Many2one('account.account', string='Cuenta', related='tax.account_id', readonly=True,)
    percentage = fields.Float(string='Porcentaje', related='tax.amount', readonly=True,)
    #amount = fields.Float(string='Porcentaje')
    amountTaxRetention = fields.Float(string='Valor impuesto retención')
    baseAmount = fields.Float(string='Base imponible')

    @api.onchange('tax', 'baseAmount')
    def calculateAmountRetention(self):
        amount = self.calculateRetentionAmount(self.percentage)
        self.amountTaxRetention = amount

    @api.onchange('tax')
    def onchangeTax(self):
        if self.typeRetention == '1':
            self.baseAmount = self.tax_id.amountUntaxed
        elif self.typeRetention == '2':
            self.baseAmount = self.tax_id.amountTax

    def calculateRetentionAmount(self, percent):
        amountRetention = percent / 100 * self.baseAmount
        return amountRetention
