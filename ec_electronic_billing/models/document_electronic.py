
import time
from odoo import models, fields, api
from . import utils

class DocoumentElectronic(models.Model):

    _name = 'document.electronic'

    def _get_acive_api_sri(self, company):
        """Get ws sri test o prodcution"""
        if company.env_type == '1':
            return company.url_test
        else:
            return company.url_production

    def get_secuencial(self):
        """Return secuencial invoice"""
        sequence = 0
        if self.invoice_number:
            number_invoice = self.invoice_number.split("-")
            return number_invoice[-1]
        if self.type_document() == 'invoice':
            sequence = self.code_emission.current_number_invoice + 1
        elif self.type_document() == 'note_credit':
            sequence = self.code_emission.current_credit_note + 1
        next_num_invoice = str(sequence)

        return next_num_invoice.rjust(9, '0')

    def get_access_key(self, name):
        """Get code access sri"""
        env_config = self.company_id


        date_invoice = self.date_order_local.split()[0].split('-')
        if name == 'invoice':
            type_comp = utils.tipoDocumento['01']
        elif name == 'note_credit':
            type_comp = utils.tipoDocumento['04']
        elif name == 'retention':
            type_comp = utils.tipoDocumento['18']

        date_invoice.reverse()
        date_fmt = ''.join(date_invoice)
        ruc = self.company_id.partner_id.vat
        series = '{}{}'.format(self.code_emission.number_establishment.number_establish,
                               self.code_emission.code_emission)
        number = self.get_secuencial()
        code_num = str(self.id)
        type_emission = self.code_emission.type_emision
        self._logger.info("info access key {} {} {} {}". format(type_comp, ruc, env_config.env_type, series))
        access_key = (
            [date_fmt, type_comp, ruc, env_config.env_type],
            [series, number, code_num.rjust(8, '0'), type_emission]
        )
        return access_key

    @api.multi
    def _get_codes(self, name='invoice'):
        ak_temp = self.get_access_key(name)
        if self.access_key:
            access_key = self.access_key
        else:
            access_key = self.SriServiceObj.create_access_key(ak_temp)
        emission_code = self.code_emission.code_emission
        return access_key, emission_code

    @staticmethod
    def get_type_document_invoice(type_document):
        """"Return type of type document"""
        if type_document == 'invoice':
            return utils.tipoDocumento['01']
        elif type_document == 'note_credit':
            return utils.tipoDocumento['04']

    def _info_tributaria(self, document):

        company = self.company_id
        access_key, emission_code = self._get_codes(document)
        info_tributary = {
            'ambiente': company.env_type,
            'razonSocial': company.full_name,
            'nombreComercial': company.name_comercial,
            'ruc': company.partner_id.vat,
            'claveAcceso': access_key,
            'tipoEmision': self.code_emission.type_emision,
            'codDoc': self.get_type_document_invoice(document),
            'estab': self.code_emission.number_establishment.number_establish,
            'ptoEmi': self.code_emission.code_emission,
            'secuencial': self.get_secuencial(),
            'dirMatriz': self.company_id.street
        }
        return info_tributary

    def _detalles(self):
        """Esctructura XML detalle factura"""

        def fix_chars(code):
            special = [
                [u'%', ' '],
                [u'º', ' '],
                [u'Ñ', 'N'],
                [u'ñ', 'n']
            ]
            for f, r in special:
                code = code.replace(f, r)
            return code

        detalles = []
        for line in self.invoice_line_ids:

            codigoPrincipal = line.product_id and line.product_id.default_code and \
                              fix_chars(line.product_id.default_code)
            priced = line.price_unit * (1 - (line.discount or 0.00) / 100.0)
            discount = (line.price_unit - priced) * line.quantity
            detalle = {
                'codigoPrincipal': codigoPrincipal[:25],
                'descripcion': fix_chars(line.product_id.name),  # TODO code aux
                'cantidad': '%.6f' % (line.quantity),
                'precioUnitario': '%.6f' % (line.price_unit),
                'descuento': '%.2f' % discount,
                'precioTotalSinImpuesto': '%.2f' % (line.price_subtotal)
            }
            impuestos = []

            total_tax_cero = 0
            total_tax_12 = 0
            for tax_line in line.invoice_line_tax_ids:
                if tax_line.name == 'IVA 12':
                    total_tax_12 += tax_line.amount
                    node_tax_12 = {
                        'codigo': utils.tabla16[tax_line.name],
                        'codigoPorcentaje': utils.tabla17[tax_line.name],  # TODO VERIFICAR
                        'baseImponible': '{:.2f}'.format(line.price_subtotal),
                        'tarifa': '{:.2f}'.format(tax_line.amount),
                        'valor': '{:.2f}'.format(line.price_subtotal * tax_line.amount/100)
                    }
                if tax_line.name == 'IVA 0':
                    total_tax_cero += tax_line.amount
                    node_tax_0 = {
                        'codigo': utils.tabla16[tax_line.name],
                        'codigoPorcentaje': utils.tabla17[tax_line.name],
                        'baseImponible': '{:.2f}'.format(line.price_subtotal),
                        'tarifa': '{:.2f}'.format(tax_line.amount),
                        'valor': '0.00'
                    }

            if total_tax_cero > 0:
                impuestos.append(node_tax_0)
            if total_tax_12 > 0:
                impuestos.append(node_tax_12)

            detalle.update({'impuestos': impuestos})
            detalles.append(detalle)
        return {'detalles': detalles}
