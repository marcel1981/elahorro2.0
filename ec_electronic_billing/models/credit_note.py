import time
import os
import logging
from jinja2 import Environment, FileSystemLoader
from odoo import models, fields, api

from ..sri.sri import DocumentXML, SriService
from ..sri.xades import Xades
from . import utils
import pdb

class NoteCredit(models.Model):
    _name = 'account.invoice'
    _inherit = ['account.invoice', 'document.electronic']

    # call object sri
    SriServiceObj = SriService()

    def _info_factura(self):
        """Esctructura XML informacion"""

        # set date format y-m-d
        def fix_date(date):
            date_format = time.strftime('%d/%m/%Y', time.strptime(date, '%Y-%m-%d'))
            return date_format

        company = self.company_id
        
        partner = self.partner_id
        # calculate amount_untaxed
        document = self.get_document_invoice('credit_note')
        amount_untaxed = self.amount_total - self.amount_tax
        origin_invoice = self.creditNoteDocResource
        info_invoice = {
            'fechaEmision': fix_date(self.date_order_local.split()[0]),
            'dirEstablecimiento': "{} {}".format(company.street, company.street2),
            'obligadoContabilidad': company.keep_accounting,
            'tipoIdentificacionComprador': partner.type_identifier,
            'razonSocialComprador': partner.name,
            'identificacionComprador': partner.identification,
            'totalSinImpuestos': '%.2f' % (amount_untaxed),
            'moneda': 'DOLAR',#TODO review
        }

        if self.type_document() == 'invoice':
            info_aditional = {
                'direccionComprador': str(partner.contact_address).replace('\n', ' '),
                'totalDescuento': '0.00',
                'propina': '0.00',#TODO review
                'importeTotal': '{:.2f}'.format(self.amount_total),
            }
            info_invoice.update(info_aditional)
            info_invoice.update({'formaPago': self._payment_methods()})

        elif self.type_document() == 'note_credit':

            credit_note = {
                'codDocModificado': document,
                'numDocModificado': origin_invoice.invoice_number,
                'fechaEmisionDocSustento': fix_date(origin_invoice.date_order_local.split()[0]),

                'valorModificacion': self.amount_total,
                'motivo': self.name,
            }
            info_invoice.update(credit_note)


        if company.company_registry:
            info_invoice.update({'contribuyenteEspecial': company.company_registry})

        totalConImpuestos = []
        total_tax_cero = 0
        total_tax_12 = 0
        subtotalTax12 = 0
        subtotalTax0 = 0
        for line in self.invoice_line_ids:
            for tax_line in line.invoice_line_tax_ids:
                value = line.price_subtotal * tax_line.amount/100
                subtotalTax12 += line.price_subtotal
                if tax_line.name == 'IVA 12':
                    total_tax_12 += value
                    node_tax_12 = {
                        'codigo': utils.tabla16[tax_line.name],
                        'codigoPorcentaje': utils.tabla17[tax_line.name],
                        'baseImponible': '{:.2f}'.format(subtotalTax12),
                        #'tarifa': '{:.2f}'.format(tax_line.amount),
                        'valor': '{:.2f}'.format(total_tax_12)
                    }
                if tax_line.name == 'IVA 0':
                    total_tax_cero += value
                    subtotalTax0 += line.price_subtotal
                    node_tax_0 = {
                        'codigo': utils.tabla16[tax_line.name],
                        'codigoPorcentaje': utils.tabla17[tax_line.name],
                        'baseImponible': '{:.2f}'.format(subtotalTax0),
                        #'tarifa': '{:.2f}'.format(tax_line.amount),
                        'valor': '0.00'
                    }

        if total_tax_cero > 0:
            totalConImpuestos.append(node_tax_0)
        if total_tax_12 > 0:
            totalConImpuestos.append(node_tax_12)

        info_invoice.update({'totalConImpuestos': totalConImpuestos})
        return info_invoice
