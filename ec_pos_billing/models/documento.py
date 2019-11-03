import base64
import logging
import pdb
import time

from . import utils

sfrom odoo import models, fields, api

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class ElectronicDocument(models.AbstractModel):
    _name = 'invoice.document'
    _logger = logging.getLogger('invoice.document')

    access_key = fields.Char('Clave de Acceso', size=49, readonly=True)

    def get_secuencial(self):
        """Return secuencial invoice"""
        if self.invoice_number:
            number_invoice = self.invoice_number.split("-")
            return number_invoice[-1]
        config_invoice_pos = self._config_establishment()
        sequence = config_invoice_pos.current_number_invoice + 1
        next_num_invoice = str(sequence)
        return next_num_invoice.rjust(9, '0')

    def get_access_key(self, name):
        """Get code access sri"""
        company = self.company_id
        config_pos = self._config_establishment()
        if name == 'invoice':
            date_invoice = self.date_order_local.split()[0].split('-')
            type_comp = utils.tipoDocumento['01']
        elif name == 'retention':
            pass
        date_invoice.reverse()
        date_fmt = ''.join(date_invoice)
        ruc = self.company_id.partner_id.vat
        series = '{}{}'.format(config_pos.number_establishment.number_establish, config_pos.code_emission)
        number = self.get_secuencial()
        code_num = str(self.id)
        type_emission = config_pos.type_emision
        self._logger.info("info access ke {} {} {} {}".format(type_comp, ruc, company.env_type, series))
        access_key = (
            [date_fmt, type_comp, ruc, company.env_type],
            [series, number, code_num.rjust(8, '0'), type_emission]
        )
        return access_key

    @api.multi
    def _get_codes(self, name='invoice'):
        ak_temp = self.get_access_key(name)
        config_pos = self._config_establishment()
        if self.access_key:
            access_key = self.access_key
        else:
            access_key = self.SriServiceObj.create_access_key(ak_temp)
        emission_code = config_pos.code_emission
        return access_key, emission_code

    @staticmethod
    def get_document_invoice(document):
        """"Return type of document"""
        if document == 'invoice':
            return utils.tipoDocumento['01']

    def _info_tributaria(self, document):
        company = self.company_id
        access_key, emission_code = self._get_codes('invoice')
        config_pos = self._config_establishment()
        info_tributary = {
            'ambiente': company.env_type,
            'razonSocial': company.full_name,
            'nombreComercial': company.name_comercial,
            'ruc': company.partner_id.vat,
            'claveAcceso': access_key,
            'codDoc': self.get_document_invoice(document),
            'estab': config_pos.number_establishment.number_establish,
            'ptoEmi': config_pos.code_emission,
            'secuencial': self.get_secuencial(),
            'dirMatriz': company.street
        }
        return info_tributary

    def _payment_methods(self, order):
        """payments methods order"""
        pay_method = []
        amount_cash = 0
        for pay_met in order.statement_ids:

            if pay_met.journal_id.code == '01':
                amount_cash += pay_met.amount
            elif pay_met.journal_id.isJournalCreditNote:
                line_pay = {
                    'formaPago': '01',
                    'total': '{:.2f}'.format(pay_met.amount)
                }
                pay_method.append(line_pay)

            elif pay_met.amount > 0 and not pay_met.journal_id.isJournalCreditNote:
                line_pay = {
                    'formaPago': pay_met.journal_id.code,
                    'total': '{:.2f}'.format(pay_met.amount)
                }
                pay_method.append(line_pay)

        if amount_cash > 0:
            line_pay = {
                'formaPago': '01',
                'total': '{:.2f}'.format(amount_cash)
            }
            pay_method.append(line_pay)


        return pay_method

    def _info_factura(self, order):
        """Esctructura XML informacion"""

        # set date format y-m-d
        def fix_date(date):
            date_format = time.strftime('%d/%m/%Y', time.strptime(date, '%Y-%m-%d'))
            return date_format

        company = order.company_id
        partner = order.partner_id
        config_pos = self._config_establishment()
        # calculate amount_untaxed
        amount_untaxed = self.amount_total - self.amount_tax
        info_invoice = {
            'fechaEmision': fix_date(order.date_order_local.split()[0]),
            'dirEstablecimiento': config_pos.number_establishment.address_store,
            'obligadoContabilidad': company.keep_accounting,
            'tipoIdentificacionComprador': partner.type_identifier,
            'razonSocialComprador': partner.name,
            'identificacionComprador': partner.identification,
            'direccionComprador': str(partner.contact_address).replace('\n', ' '),
            #'totalSinImpuestos': '%.2f' % (amount_untaxed),
            'totalSinImpuestos': '%.2f' % (amount_untaxed),
            'totalDescuento': '0.00',
            'propina': '0.00',
            'importeTotal': '{:.2f}'.format(order.amount_total),
            #'importeTotal': '56',
            'moneda': 'DOLAR'
        }

        info_invoice.update({'formaPago': self._payment_methods(order)})
        if company.company_registry:
            info_invoice.update({'contribuyenteEspecial': company.company_registry})

        totalConImpuestos = []
        total_tax_cero = 0
        total_tax_12 = 0
        total_12 = 0
        for tax in self.lines:
            value = tax.price_subtotal * tax.tax_ids_after_fiscal_position.amount / 100
            if tax.tax_ids_after_fiscal_position.name == 'IVA 12':
                total_tax_12 += value
                total_12 += tax.price_subtotal
                node_tax_12 = {
                    'codigo': utils.tabla16[tax.tax_ids_after_fiscal_position.name],
                    'codigoPorcentaje': utils.tabla17[tax.tax_ids_after_fiscal_position.name],
                    'baseImponible': '{:.2f}'.format(total_12),
                    # TODO 'tarifa': '{:.2f}'.format(tax.tax_ids_after_fiscal_position.amount),
                    'valor': '{:.2f}'.format(total_tax_12)
                }
            if tax.tax_ids_after_fiscal_position.name == 'IVA 0':
                total_tax_cero += tax.price_subtotal
                node_tax_0 = {
                    'codigo': utils.tabla16[tax.tax_ids_after_fiscal_position.name],
                    'codigoPorcentaje': utils.tabla17[tax.tax_ids.name],
                    'baseImponible': '{:.2f}'.format(total_tax_cero),
                    'valor': '0.00'
                }


        if total_tax_cero > 0:
            totalConImpuestos.append(node_tax_0)
        if total_tax_12 > 0:
            totalConImpuestos.append(node_tax_12)

        info_invoice.update({'totalConImpuestos': totalConImpuestos})
        return info_invoice

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
        for line in self.lines:
            codigoPrincipal = line.product_id and line.product_id.default_code and \
                              fix_chars(line.product_id.default_code)
            priced = line.price_unit * (1 - (line.discount or 0.00) / 100.0)
            discount = (line.price_unit - priced) * line.qty
            if not codigoPrincipal:
                codigoPrincipal = 'Cod. no generado'
            else:
                codigoPrincipal = codigoPrincipal[:25]
            detalle = {
                'codigoPrincipal': codigoPrincipal,
                'descripcion': fix_chars(line.product_id.name),  # TODO code aux
                'cantidad': '%.6f' % (line.qty),
                'precioUnitario': '%.6f' % (line.price_unit),
                'descuento': '%.2f' % discount,
                'precioTotalSinImpuesto': '%.2f' % (line.price_subtotal)
            }
            impuestos = []
            for tax_line in line.tax_ids:
                if tax_line.name in utils.tabla17:
                    code_tax = utils.tabla17[tax_line.name]
                else:
                    code_tax = utils.tabla17['IVA 0']

                value = line.price_subtotal * tax_line.amount / 100
                impuesto = {
                    'codigo': code_tax,
                    'codigoPorcentaje': code_tax,  # TODO test
                    'tarifa': tax_line.amount,
                    'baseImponible': '{:.2f}'.format(line.price_subtotal),
                    'valor': '{:.2f}'.format(value)
                }
                impuestos.append(impuesto)
            detalle.update({'impuestos': impuestos})
            detalles.append(detalle)
        return {'detalles': detalles}

    def add_attachment(self, xml):
        """email attachment xml and pdf"""
        buffer_xml = base64.encodestring(xml.encode()).decode().replace('\n', '')
        attach = self.env['ir.attachment'].create(
            {
                'name': '{0}.xml'.format(self.access_key),
                'datas': buffer_xml,
                'datas_fname': '{0}.xml'.format(self.access_key),
                'res_model': self._name,
                'res_id': self.id,
                'type': 'binary'
            },
        )
        return attach

    def send_mail_to_client(self):
        ir_model_data = self.env['ir.model.data']
        email_tmp_obj = self.pool.get('email.template')

        context = self._context.copy()
        context['base_url'] = self.env['ir.config_parameter'].get_param('web.base.url')
        # Obtain the accion for the related object to mail
        context['action_id'] = ir_model_data.get_object_reference('addon', 'object_acction')[1]
        # Obtain Id template
        template_id = ir_model_data.get_object_reference('addon', 'email_template_invoice')[1]
        mail = email_tmp_obj.with_context(context)
        self.pool.get('email.template').send_mail(self._cr, self._uid,
                                                  template_id, self.id, force_send=True, context=context)
        return True
