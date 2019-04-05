# -*- coding: utf-8 -*-
import base64
import os
import time
import pytz
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from . import utils
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from ..sri.sri import DocumentXML, SriService
from ..sri.xades import Xades
import logging
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import pdb
logger = logging.getLogger(__name__)

class Retention(models.Model):
    _name = 'invoice.retention'
    _order = 'date desc'
    invoicePartner = fields.Many2one('account.invoice', string='Factura Proveedor',
                                     required=True,
                                     domain=[('type', '=', 'in_invoice')])

    def defaultPointEmission(self):
        return self.env['invoice.point.emission'].search([('is_retention', '=', True)])[-1]

    partner = fields.Many2one('res.partner', string='Proveedor', related='invoicePartner.partner_id', required=True)
    identifier = fields.Char(string='Identificación', related='invoicePartner.identification', readonly=True)
    dateInvoice = fields.Datetime('Fecha factura proveedor', readonly=True,  related='invoicePartner.date_order_local')
    establishment = fields.Many2one(string='Establecimiento', related='code_emission.number_establishment')
    code_emission = fields.Many2one('invoice.point.emission', 'Punto de Emision', default=defaultPointEmission)
    state = fields.Selection([('draft', 'Borrador'),
                              ('done', 'Validado'),
                              ('cancel', 'Anulado')],
                             readonly=True,
                             string='Estado',
                             default='draft')
    sri_response = fields.Selection([('1', 'No Enviado'),
                                     ('2', 'Enviado realizado'),
                                     ('3', 'Autorizado'),
                                     ('4', 'Notificado'),
                                     ('5', 'Enviado rechazado'),
                                     ('6', 'No autorizado'),
                                     ('7', 'Fact. Fisica'),
                                     ],
                                    string='Estado SRI',
                                    default='1')
    access_key = fields.Char('Clave de Acceso', size=49, readonly=True)
    STATES_VALUE = {'draft': [('readonly', False)]}
    tax_ids = fields.One2many('account.retention.tax', 'tax_id', 'Detalle de Impuestos',
                              copy=False,
                              readonly=True,
                              states={'draft': [('readonly', False)]})

    amountUntaxed = fields.Float(string='Base Imponible', compute='calculateAmountUntaxed')
    amountTax = fields.Float(string='Valor impuesto IVA', compute='calculateAmounTax')
    amountTaxRetention = fields.Float(string='Valor total Retención', compute='calculateTotalRetention')
    total = fields.Float(string='Total Fact. Proveedor', compute='calculateTotal')
    totalRetentionIva = fields.Float(string='Total Retencion IVA', compute='calculateTotalRetentionIva')
    totalRetentionBaseImponible = fields.Float(string='Total Retención Base imponible', compute='calculateTotalRetentionBaseImponible')
    local_tz = pytz.timezone('America/Guayaquil')
    ec_time = datetime.now(local_tz)
    date = fields.Datetime('Fecha', required=False, default=ec_time)

    numberRetention = fields.Char('Número de Retención', size=49, readonly=True)
    numberAuthorization = fields.Char('Número de Autorización', size=49)
    codDocSutent = fields.Char('Código Número Sustento', size=15, readonly=True,
                               states={'draft': [('readonly', False)]},
                               required=True)

    xmlSriRequestId = fields.Many2one("sri.xml.send", "SRI XML Request")
    sendMailclient = fields.Boolean("Notificación correo", default=False)
    amountRetentionDifference = fields.Float(string='Diferencia Retención')

    journal = fields.Many2one("account.journal", "Diario", readonly=True)
    user = fields.Many2one("res.users", "Responsable", related='invoicePartner.user_id', readonly=True)
    account = fields.Many2one("account.account", "Cuenta", related='invoicePartner.account_id', readonly=True)
    move = fields.Many2one("account.move", "Asiento Contable", readonly=True)
    dateEmisionSri = fields.Date('Date emisión', required=False, readonly=True, related='invoicePartner.date_invoice')
    fiscalPeriod = fields.Char(string='Periodo Fiscal')
    dateAuth = fields.Char(string='Fecha de Auth')

    TEMPLATES = {
        'retention': 'retention.xml'
    }
    typeDoc = '18'
    type = 'retention'

    @api.one
    def calculateTotalRetentionIva(self):
        amount = 0
        for tax in self.tax_ids:
            if tax.tax.typeRetention == '2':
                amount += self.calculateRetentionIva(tax.percentage)
        self.totalRetentionIva = amount

    @api.one
    def calculateTotalRetentionBaseImponible(self):
        amount = 0
        for tax in self.tax_ids:
            if tax.tax.typeRetention == '1':
                amount += self.calculateRetentionRent(tax.percentage)
        self.totalRetentionBaseImponible = amount

    @api.constrains('codDocSutent')
    def checkCodDocSutent(self):
        for record in self:
            if record.codDocSutent:
                if not record.codDocSutent.isdigit():
                    raise ValidationError("Código sustento debe ser solo números: %s" % record.codDocSutent)
                if len(record.codDocSutent) != 15:
                    raise ValidationError("Código sustento debe ser 15 digitos")

    @api.multi
    def unlink(self):
        for invoice in self:
            if invoice.state not in ('draft', 'cancel'):
                raise UserError(_(
                    'No puede eliminar una factura que no sea borrador o cancelada. Debería emitir una rectificativa en su lugar.'))
            elif invoice.move:
                raise UserError(_(
                    'No puede eliminar una factura después de que haya sido validada (y haya recibido un número). Puede volver a '
                    'establecerlo en el estado Borrador y modificar su contenido, luego volver a confirmarlo.'))
        return super(Retention, self).unlink()

    @api.onchange('partner')
    def defaultAmountRetentionDiference(self):
        self.amountRetentionDifference = self.invoicePartner.amount_untaxed

    @api.onchange('tax_ids')
    def onchangeAmountRetentionDifference(self):
        amount = self.invoicePartner.amount_untaxed
        for taxLine in self.tax_ids:
            if taxLine.typeRetention == '1':
                amount -= taxLine.baseAmount
                self.amountRetentionDifference = amount

    @api.constrains('numberAuthorization')
    def checkNumberAuthorization(self):
        for record in self:
            if record.numberAuthorization:
                if not record.numberAuthorization.isdigit():
                    raise ValidationError("Número debe ser solo números: %s" % record.numberAuthorization)

    def checkIfExistEstablishment(self):
        if not self.establishment:
            #sri_xml = self.create_envio('Configure un establecimiento para el envío de la factura al sri', 'No')
            #self.xml_sri_request_id = sri_xml
            return False
        return True

    def sumSequenceConfigEstablishment(self):
        """refresh sequence configuration of establishment"""
        self.code_emission.currentRetention += 1

    def getSequence(self):
        """Return secuencial invoice"""
        next_num_invoice = str(self.code_emission.currentRetention + 1)
        return next_num_invoice.rjust(9, '0')

    def formatInverseDate(self, date):
        date_invoice = date.split()[0].split('-')
        date_invoice.reverse()
        date_fmt = ''.join(date_invoice)
        return date_fmt

    def type_document(self):
        return 'retention'

    def getAccessKey(self):
        """Get code access sri"""
        envConfig = self.invoicePartner.company_id
        date_fmt = self.formatInverseDate(self.date)
        type_comp = utils.tipoDocumento[self.typeDoc]
        ruc = envConfig.partner_id.vat
        series = '{}{}'.format(self.code_emission.number_establishment.number_establish,
                               self.code_emission.code_emission)
        number = self.getSequence()
        code_num = str(self.id)
        type_emission = self.code_emission.type_emision
        #self._logger.info("info access key {} {} {} {}". format(type_comp, ruc, envConfig.env_type, series))
        access_key = (
            [date_fmt, type_comp, ruc, envConfig.env_type],
            [series, number, code_num.rjust(8, '0'), type_emission]
        )
        return access_key

    SriServiceObj = SriService()

    @api.multi
    def getCodes(self):
        ak_temp = self.getAccessKey()
        access_key = self.SriServiceObj.create_access_key(ak_temp)
        emission_code = self.code_emission.code_emission
        return access_key, emission_code

    @api.one
    def validateDocument(self):

        journal = self.env['account.journal'].search([('isJournalRetention', '=', True)])[-1]
        if len(self.tax_ids) < 1:
            raise ValidationError('Debe ingresar al menos un impuesto a la retención')
        if self.amountRetentionDifference == 0.0:
            pass
        else:
            raise ValidationError('Revisar el valor total de la base imponible')

        if journal:
            ref = self.invoicePartner.number
            mode_id = self.createAccountMove(journal.id, self.date, ref)
            self.state = 'done'
            self.journal = journal.id
            self.move = mode_id.id

    @api.one
    def dictionaryJournalItem(self):
        linesAccount = []
        amountRetention = self.sumIvaRetencion()
        accountInvoiceVendor = self.invoicePartner
        lineMoveInvoiceVendor = (0, 0, {'name': accountInvoiceVendor.name or '/',
                                     'debit': amountRetention,
                                     'credit': 0,
                                     'account_id': accountInvoiceVendor.account_id.id,
                                     'partner_id': accountInvoiceVendor.partner_id.id})

        journal = self.env['account.journal'].search([('isJournalRetention', '=', True)])[-1]

        for account in self.tax_ids:
            amountRetention = self.typeRetention(account)
            lineMove = (0, 0, {'name': account.account.name or '/',
                              'debit': 0,
                              'credit': amountRetention[0],
                              'account_id': account.account.id,
                              'partner_id': accountInvoiceVendor.partner_id.id})
            linesAccount.append(lineMove)
        linesAccount.append(lineMoveInvoiceVendor)
        return linesAccount


    @api.one
    @api.depends('tax_ids')
    def calculateAmountUntaxed(self):
        self.amountUntaxed = self.invoicePartner.amount_untaxed

    @api.one
    def calculateAmounTax(self):
        self.amountTax = self.invoicePartner.amount_tax

    @api.one
    def calculateTotalRetention(self):
        self.amountTaxRetention = self.sumIvaRetencion()

    @api.one
    def calculateTotal(self):
        self.total = self.invoicePartner.amount_total

    def calculateRetentionRent(self, percent):
        amountRetention = percent / 100 * self.amountUntaxed
        return amountRetention

    def calculateRetentionIva(self, percent):
        amountRetention = percent/100 * self.amountTax
        return amountRetention

    def sumIvaRetencion(self):
        amountTotalRetention = 0
        for taxLine in self.tax_ids:
            amountTotalRetention += self.typeRetention(taxLine)[0]
        return amountTotalRetention


    @api.one
    def signXml(self, invoice):
        company = self.establishment.company
        xades = Xades()
        file_pk12 = company.file_electronic_signature
        password = company.password_electronic_signature
        signed_document = xades.sign(invoice, file_pk12, password)
        return signed_document

    def getAciveApiSri(self, company):
        """Get ws sri test o prodcution"""
        if company.env_type == '1':
            return company.url_test
        else:
            return company.url_production

    @api.one
    def renderXML(self):
        # load xlm dir templates
        tmpl_path = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(tmpl_path))
        invoice_tmpl = env.get_template(self.TEMPLATES['retention'])
        data = {}
        # load data pos
        data.update(self.infoTributaria())
        data.update(self.infoRetention(self.invoicePartner))
        data.update(self.taxes())
        invoice = invoice_tmpl.render(data)
        return invoice

    @api.one
    def sendRetentionSri(self):
        """Enviar factura electronica al SRI"""
        for inv in self:
            if not self.checkIfExistEstablishment():
                return False
            # render xml
            #self.dateEmisionSri = datetime.now(self.local_tz)
            company = self.establishment.company
            invoice = self.renderXML()
            # valiadate xml
            inv_xml = DocumentXML(invoice[0], 'retention')
            inv_xml.validate_xml()
            # signarture xml
            signed_document = self.signXml(invoice[0])
            logger.warning('Document sign {}'.format(signed_document))
            # get env company
            api_sri = self.getAciveApiSri(company)
            if self.sri_response == '2':
                logger.warning('La factura ya fue enviada al SRI')
                return False
            timeout = company.max_time
            ok, response = inv_xml.send_xml_sri(signed_document[0], api_sri, timeout)

            if inv.access_key:
                access_key = inv.access_key
            else:
                access_key, emission_code = self.getCodes()
            #self._logger.info("access key {}".format(access_key))
            #pdb.set_trace()
            sri_xml = self.invoicePartner.create_envio(response, signed_document[0])
            self.xmlSriRequestId = sri_xml[0]

            if not ok:
                #self._logger.info('Errores {}'.format(response))
                self.sri_response = '5'
                return False
            self.access_key = access_key
            self.sri_response = '2'
            self.numberRetention = "{}-{}-{}".format(self.code_emission.number_establishment.number_establish,
                                                     self.code_emission.code_emission,
                                                     self.getSequence())
            self.sumSequenceConfigEstablishment()
            return True

    @api.one
    def sendAuthorization(self):
        document = DocumentXML('doc', 'retention')
        access_key = self.access_key
        company = self.establishment.company
        api_sri = self.getAciveApiSri(company)

        if access_key:
            state, auth_xml, sms = document.request_authorization(access_key, api_sri)
            if not state:

                self.sri_response = '5'
                self.xmlSriRequestId.sri_auth = sms

            if state:
                self.sri_response = '3'
                if not self.sendMailclient:
                    atts = []
                    file_name = 'FV#{}'.format(self.access_key)
                    attach_xml = self.createAttachment(auth_xml, file_name, self.id)
                    atts.append(attach_xml)
                    attach_pdf = self.createAttachmentPdf(file_name, self)
                    atts.append(attach_pdf)
                    send_mail = self.invoicePartner.send_email(self.invoicePartner, attachments=[(4, a.id) for a in atts])
                    if send_mail:
                        self.sendMailclient = True
                if self.xmlSriRequestId:
                    #pdb.set_trace()
                    self.xmlSriRequestId.sri_xml_response = auth_xml
                    self.xmlSriRequestId.sri_auth = sms


    @api.one
    def sendInvoiceAuthorization(self):
        if self.sri_response in ['1', '5', '6']:
            self.sendRetentionSri()
        if self.sri_response in ['2', '5']:
            self.sendAuthorization()

    def infoTributaria(self):
        company = self.establishment.company
        access_key, emission_code = self.getCodes()
        info_tributary = {
            'ambiente': company.env_type,
            'razonSocial': company.full_name,
            'nombreComercial': company.name_comercial,
            'ruc': company.partner_id.vat,
            'claveAcceso': access_key,
            'tipoEmision': self.code_emission.type_emision,
            'codDoc': utils.tipoDocumento['18'],
            'estab': self.code_emission.number_establishment.number_establish,
            'ptoEmi': self.code_emission.code_emission,
            'secuencial': self.getSequence(),
            'dirMatriz': self.establishment.company.street
        }
        return info_tributary

    def fix_date(self, date):
        date_format = time.strftime('%d/%m/%Y', time.strptime(date, '%Y-%m-%d'))
        return date_format

    def infoRetention(self, invoice):

        """
        """
        # generar infoTributaria
        company = invoice.company_id
        partner = invoice.partner_id
        dateFiscalFormat = time.strftime('%m/%Y', time.strptime(self.dateEmisionSri, '%Y-%m-%d'))
        infoCompRetencion = {
            'fechaEmision': self.fix_date(self.date.split()[0]),
            'dirEstablecimiento': company.street,
            'obligadoContabilidad': 'SI',
            'tipoIdentificacionSujetoRetenido': partner.type_identifier,#TODO,
            'razonSocialSujetoRetenido': partner.name,
            'identificacionSujetoRetenido': partner.identification,
            'periodoFiscal': dateFiscalFormat,
        }
        self.fiscalPeriod = dateFiscalFormat
        self.dateAuth = self.fix_date(self.dateEmisionSri.split()[0])
        #if company.company_registry:
        #   infoCompRetencion.update({'contribuyenteEspecial': company.company_registry})  # noqa
        return infoCompRetencion

    def taxes(self):
        """def get_codigo_retencion(linea):
            if linea.tax_id.tax_group_id in ['ret_vat_b', 'ret_vat_srv']:
                return utils.tabla21[line.percent]
            else:
                code = linea.base_code_id and linea.base_code_id.code or linea.tax_code_id.code  # noqa
                return code"""

        impuestos = []
        for taxLine in self.tax_ids:
            amountRetention = self.typeRetention(taxLine)
            impuesto = {
                'codigo': taxLine.typeRetention,
                'codigoRetencion': taxLine.tax.codeSRI,
                'baseImponible': '%.2f' % (taxLine.baseAmount),
                'porcentajeRetener': str(taxLine.percentage),
                'valorRetenido': '%.2f' % (taxLine.amountTaxRetention),
                'codDocSustento': '01', #TODO
                'numDocSustento': self.codDocSutent,
                'fechaEmisionDocSustento': self.fix_date(self.dateEmisionSri),# noqa
            }
            impuestos.append(impuesto)
        return {'impuestos': impuestos}

    @api.one
    def typeRetention(self, tax):

        if tax.tax.typeRetention == '1':
            amount = self.calculateRetentionRent(tax.percentage)
        elif tax.tax.typeRetention == '2':
            amount = self.calculateRetentionIva(tax.percentage)
        else:
            return 0
        return amount

    @api.multi
    def getXmlfile(self):

        url_path = '/download/xml/retention/{}'.format(self.id)
        a = {
            'type': 'ir.actions.act_url',
            'url': url_path,
            'target': 'self',
        }
        return a

    def createAttachment(self, xml_element, name, id, model='invoice.retention'):
        """Create attachement xml for client"""
        buf = StringIO()
        xml = str(xml_element)
        buf.write(xml)
        data = base64.b64encode(xml.encode('ISO-8859-1'))
        filename = (name + '.xml').replace(' ', '')
        url_path = '/download/xml/retention/{}'.format(id)
        att = self.env['ir.attachment'].create(
            dict(
                name='{0}.xml'.format(filename),
                url=url_path,
                datas_fname=filename,
                res_model=model,
                res_id=id,
                type='binary',
                datas=data,)
        )
        return att

    @api.multi
    def createAttachmentPdf(self, name, invoice, model='account.invoice'):
        if invoice.type_document() == 'retention':
            data, data_format = self.env.ref('ec_electronic_billing.account_retention').render([invoice.id])
        att = self.env['ir.attachment'].create(
            dict(
                name='{0}.pdf'.format(name),
                datas_fname='{0}.pdf'.format(name),
                res_model=model,
                res_id=invoice.id,
                type='binary',
                datas=base64.encodestring(data),
                mimetype='application/x-pdf')
        )
        return att

    @api.multi
    def printRetention(self):
            reportRetention = self.env.ref('ec_electronic_billing.account_retention').report_action(self)
            if reportRetention:
                logger.info('Print Report {}'.format(reportRetention))
                return self.env.ref('ec_electronic_billing.account_retention').report_action(self)
            self.createAttachmentPdf('none', self)
            logger.info('Print Reports {}'.format(reportRetention))
            return self.env.ref('ec_electronic_billing.account_retention').report_action(self)



    def createAccountMove(self, journal, date, ref):
        linesMoveAccount = self.dictionaryJournalItem()
        move = {'ref': ref,
                'journal_id': journal,
                'date': date,
                'line_ids': linesMoveAccount[0]
                }
        logger.info("Account move lines {}".format(move))
        move_id = self.env['account.move'].create(move)
        move_id.post()
        return move_id

    def reverseAccountMove(self):
        #journal = self.env['account.journal'].search([('isJournalRetention', '=', True)])[-1]
        #mode_id = self.createAccountMove(journal.id, self.date, ref)
        #linesMoveAccount = self.dictionaryJournalItemReverse()
        #ref = self.invoicePartner.number
        #move = {'ref': "Inversa de: {}".format(ref),
        #        'journal_id': journal.id,
        #        'date': self.date,
        #        'line_ids': linesMoveAccount[0]
        #        }
        #logger.info("Account move lines {}".format(move))
        #move_id = self.env['account.move'].create(move)
        #move_id.post()
        #self.state = 'cancel'
        #sql = ''
        #self._cr.execute("DELETE FROM account_move_book_tax WHERE book_id=%s", (self.id,))
        if self.move:
            self.env.cr.execute("DELETE FROM account_move WHERE id=%s", (self.move.id,))
            self.state = 'cancel'

        #self.env.cr.fetchall()
        return True

    @api.one
    def dictionaryJournalItemReverse(self):
        linesAccount = []
        amountRetention = self.sumIvaRetencion()
        accountInvoiceVendor = self.invoicePartner
        lineMoveInvoiceVendor = (0, 0, {'name': accountInvoiceVendor.name or '/',
                                        'debit': 0,
                                        'credit': amountRetention,
                                        'account_id': accountInvoiceVendor.account_id.id,
                                        'partner_id': accountInvoiceVendor.partner_id.id})
        for account in self.tax_ids:
            amountRetention = self.typeRetention(account)
            lineMove = (0, 0, {'name': account.account.name or '/',
                               'debit': amountRetention[0],
                               'credit': 0,
                               'account_id': account.account.id,
                               'partner_id': accountInvoiceVendor.partner_id.id})
            linesAccount.append(lineMove)
        linesAccount.append(lineMoveInvoiceVendor)
        return linesAccount






