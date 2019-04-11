# -*- coding: utf-8 -*-
import base64
import logging
import os
from datetime import datetime

import pytz
from dateutil import tz
from jinja2 import Environment, FileSystemLoader

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

from ..sri.sri import DocumentXML, SriService
from ..sri.xades import Xades
from . import utils

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class AccountInvoice(models.Model):
    _name = "account.invoice"
    _inherit = "account.invoice"
    _logger = logging.getLogger("account.invoice")

    identification = fields.Char(
        string="Identificación", related="partner_id.identification", readonly=True
    )
    msj_request = fields.Text(
        string="Mensaje Recepción", related="xml_sri_request_id.sri_receipt"
    )
    msj_auth = fields.Text(
        string="Mensaje Authorización", related="xml_sri_request_id.sri_auth"
    )
    date_order_local = fields.Datetime(
        string=_("Date current action"), required=False, readonly=True
    )
    xml_sri_request_id = fields.Many2one("sri.xml.send", "SRI XML Request")
    dateEmisionSri = fields.Datetime("Date emisión", required=False, readonly=True)
    invoice_number = fields.Char(string="Nro. Documento", store=True, copy=False)
    sri_response = fields.Selection(
        [
            ("1", "No Enviado"),
            ("2", "Enviado realizado"),
            ("3", "Autorizado"),
            ("4", "Notificado"),
            ("5", "Enviado rechazado"),
            ("6", "No autorizado"),
            ("7", "Fact. Fisica"),
        ],
        string="Estado SRI",
        default="1",
    )

    send_mail_client = fields.Boolean("Notificación correo", default=False)
    access_key = fields.Char("Clave de Acceso", size=49)
    establishment = fields.Many2one(
        string="Establecimiento", related="code_emission.number_establishment"
    )
    code_emission = fields.Many2one("invoice.point.emission", "Punto de Emision")
    physical_billing = fields.Boolean(
        "Facturación física", default=False, readonly=False
    )
    creditNoteDocResource = fields.Many2one(
        "account.invoice", "Número Fact. del cliente a afectar"
    )

    TEMPLATES = {"invoice": "invoice.xml", "note_credit": "credit_note.xml"}

    types = {"out_invoice": "invoice", "out_refund": "note_credit"}

    @api.one
    @api.constrains("creditNoteDocResource")
    def checkIfExistCreditNoteResource(self):
        if self.type == "out_refund":
            if not self.creditNoteDocResource:
                raise ValidationError("Ingrese número de factura de cliente a afectar")

    @api.onchange("physical_billing", "sri_response")
    def check_physical_billing(self):
        if self.physical_billing:
            self.physical_billing = True
            self.sri_response = "7"
        else:
            self.sri_response = "1"

    def check_if_exist_establishment(self):
        if not self.establishment:
            sri_xml = self.create_envio(
                "Configure un establecimiento para el envío de la factura al sri", "No"
            )
            self.xml_sri_request_id = sri_xml
            return False
        return True

    def type_document(self):
        if self.type == "out_invoice":
            return self.types["out_invoice"]
        elif self.type == "out_refund":
            return self.types["out_refund"]
        elif self.type == "retention":
            return "retention"

    def _sequence_config_establishment(self):
        """refresh sequence configuration of establishment"""
        type_doc = self.type_document()
        if type_doc == "invoice":
            self.code_emission.current_number_invoice += 1
        elif type_doc == "note_credit":
            self.code_emission.current_credit_note += 1

    @staticmethod
    def get_document_invoice(document):
        """"Return type of document"""
        if document == "invoice":
            return utils.tipoDocumento["01"]
        elif document == "credit_note":
            return utils.tipoDocumento["04"]

    def _payment_methods(self):
        """payments methods order"""
        pay_method = []

        if self.payment_move_line_ids:

            for pay_met in self.payment_move_line_ids:
                amount = pay_met.credit + pay_met.amount_residual

                if pay_met.journal_id.isJournalCreditNote:
                    journal_code = "01"
                else:
                    journal_code = pay_met.journal_id.code

                if amount:
                    line_pay = {
                        "formaPago": journal_code,
                        "total": "{:.2f}".format(amount),
                    }
                    pay_method.append(line_pay)
        else:
            line_pay = {"formaPago": "01", "total": "{:.2f}".format(self.amount_total)}
            pay_method.append(line_pay)

        return pay_method

    def render_document(self, type_doc):
        """Fill xml with the order"""
        # load xlm dir templates
        tmpl_path = os.path.join(os.path.dirname(__file__), "templates")
        env = Environment(loader=FileSystemLoader(tmpl_path))
        invoice_tmpl = env.get_template(self.TEMPLATES[type_doc])
        data = {}
        # load data pos
        data.update(self._info_tributaria(type_doc))
        data.update(self._info_factura())
        details = self._detalles()
        data.update(details)
        invoice = invoice_tmpl.render(data)
        return invoice

    @api.one
    def action_send_invoice(self):
        type = self.type_document()
        """Enviar factura electronica al SRI"""
        for inv in self:
            if not self.check_if_exist_establishment():
                return False
            # render xml
            invoice = self.render_document(type)
            # valiadate xml
            inv_xml = DocumentXML(invoice, type)
            inv_xml.validate_xml()
            # signarture xml
            xades = Xades()
            file_pk12 = inv.company_id.file_electronic_signature
            password = inv.company_id.password_electronic_signature
            signed_document = xades.sign(invoice, file_pk12, password)
            # get env company
            api_sri = self._get_acive_api_sri(self.company_id)
            self.dateEmisionSri = self.date_order_local
            if self.sri_response == "2":
                logging.warning("La factura ya fue enviada al SRI")
                return False
            if inv.access_key:
                access_key = inv.access_key
            else:
                access_key, emission_code = self._get_codes(type)
            self.access_key = access_key
            self._logger.info("access key {}".format(access_key))
            self.invoice_number = "{}-{}-{}".format(
                self.code_emission.number_establishment.number_establish,
                self.code_emission.code_emission,
                self.get_secuencial(),
            )
            self._sequence_config_establishment()
            timeout = self.company_id.max_time
            ok, response = inv_xml.send_xml_sri(signed_document, api_sri, timeout)
            sri_xml = self.create_envio(response, signed_document)
            self.xml_sri_request_id = sri_xml

            if not ok:
                self._logger.info("Errores {}".format(response))
                self.write({"sri_response": "5"})
                return False
            self.write({"sri_response": "2"})
            return True

    @api.one
    def sendAuthorization(self):
        type = self.type_document()
        document = DocumentXML("doc", type)
        access_key = self.access_key
        api_sri = self._get_acive_api_sri(self.company_id)
        if access_key:
            state, auth_xml, sms = document.request_authorization(access_key, api_sri)

            if not state:
                self.sri_response = "6"
                self._logger.warning("{}".format("Error en la autorizaciòn al SRI"))
                self.xml_sri_request_id.sri_auth = sms
            self._logger.info("Number Invoice {}".format(self.number))
            if self.xml_sri_request_id:
                self.xml_sri_request_id.sri_xml_response = auth_xml
                self.xml_sri_request_id.sri_auth = sms
            if state:
                if not self.send_mail_client:
                    atts = []
                    file_name = "FV#{}".format(self.access_key)
                    attach_xml = self.create_attachment(auth_xml, file_name, self.id)
                    atts.append(attach_xml)
                    attach_pdf = self.create_attachment_pdf(file_name, self)
                    atts.append(attach_pdf)
                    send_mail = self.send_email(
                        self, attachments=[(4, a.id) for a in atts]
                    )
                    if send_mail:
                        self.send_mail_client = True

                self.sri_response = "3"

    @api.one
    def sendInvoiceAuthorization(self):
        if self.sri_response in ["1", "5", "6"]:
            self.checkIfExistCreditNoteResource()
            self.action_send_invoice()
        if self.sri_response in ["2", "5", "6"]:
            self.sendAuthorization()

    @api.one
    def render_authorized_invoice(self, autorizacion):
        tmpl_path = os.path.join(os.path.dirname(__file__), "templates")
        env = Environment(loader=FileSystemLoader(tmpl_path))
        invoice_tmpl = env.get_template("authorized_invoice.xml")
        auth_xml = {
            "estado": autorizacion.estado,
            "numeroAutorizacion": autorizacion.numeroAutorizacion,
            "ambiente": autorizacion.ambiente,
            "fechaAutorizacion": str(
                autorizacion.fechaAutorizacion.strftime("%d/%m/%Y %H:%M:%S")
            ),  # noqa
            "comprobante": autorizacion.comprobante,
        }
        auth_invoice = invoice_tmpl.render(auth_xml)
        self.sri_response = "3"
        return auth_invoice

    @api.multi
    def invoice_print(self):
        if self.type_document() == "invoice":
            return self.env.ref("ec_electronic_billing.account_invoices").report_action(
                self
            )
        elif self.type_document() == "note_credit":
            return self.env.ref(
                "ec_electronic_billing.account_credit_note"
            ).report_action(self)

    @api.multi
    def get_xml_file(self):
        url_path = "/download/xml/invoice/{}".format(self.id)
        return {"type": "ir.actions.act_url", "url": url_path, "target": "self"}

    def create_attachment(self, xml_element, name, id, model="account.invoice"):
        """Create attachement xml for client"""
        buf = StringIO()
        xml = str(xml_element)
        buf.write(xml)
        data = base64.b64encode(xml.encode("ISO-8859-1"))
        filename = (name + ".xml").replace(" ", "")
        url_path = "/download/xml/invoice/%s" % id
        att = (
            self.env["ir.attachment"]
            .sudo()
            .create(
                dict(
                    name="{0}.xml".format(filename),
                    url=url_path,
                    datas_fname=filename,
                    res_model=model,
                    res_id=id,
                    type="binary",
                    datas=data,
                )
            )
        )
        return att

    @api.multi
    def create_attachment_pdf(self, name, invoice, model="account.invoice"):

        self._logger.info("VER TIPO {}".format(self.type_document()))
        if invoice.type_document() == "invoice":
            data, data_format = (
                self.env.ref("ec_electronic_billing.account_invoices")
                .sudo()
                .render([invoice.id])
            )
        elif invoice.type_document() == "note_credit":
            # data, data_format = self.env.ref('ec_electronic_billing.account_credit_note').render([invoice.id])
            data = (
                request.env.ref("ec_electronic_billing.account_credit_note")
                .sudo()
                .render_qweb_pdf([invoice.id])[0]
            )

        att = (
            self.env["ir.attachment"]
            .sudo()
            .create(
                dict(
                    name="{0}.pdf".format(name),
                    datas_fname="{0}.pdf".format(name),
                    res_model=model,
                    res_id=invoice.id,
                    type="binary",
                    datas=base64.encodestring(data),
                    mimetype="application/x-pdf",
                )
            )
        )

        return att

    def create_envio(self, menssage, res):
        """create object sent sri then show client"""
        # TODO delete duplica method pos
        envio = {"sri_receipt": menssage, "sri_xml_response": res}
        envio_id = self.env["sri.xml.send"].sudo().create(envio)
        return envio_id

    def send_email(self, invoice, attachments=[]):

        if invoice.type_document() == "invoice":
            subject = "Facturación Electrónica"
        elif invoice.type_document() == "note_credit":
            subject = "Nota de crédito"
        else:
            subject = "Retención"

        if attachments:
            self._logger.info("Send invoice by mail ")
            body_html = (
                "<p>Estimada(o) {}</p> <p>Muchas gracias por ser parte de la familia Almacenes El Ahorro, adjuntamos"
                " los comprobantes electrónicos emitidos de acuerdo a la Resolución del SRI No. "
                "NAC-DGERCGC13-00236 del 06 de mayo de 2013.</p><p>Esperamos verlo pronto en nuestros locales.</p>"
                "<p>Saludos</p><p>Almacenes El Ahorro</p>".format(
                    invoice.partner_id.name
                )
            )
            values = {
                "email_from": invoice.company_id.email,
                "email_to": invoice.partner_id.email,
                "auto_delete": False,
                "model": "account.invoice",
                "body_html": body_html,
                "subject": subject,
                "attachment_ids": attachments,
            }
            send_mail = self.env["mail.mail"].sudo().create(values)
            send_mail.send()
            return True


class InvoiceReport(models.AbstractModel):
    _name = "report.module.report_name"

    @api.multi
    def invoice_print(self, docids, data=None):
        report_obj = self.env["report"]
        report = report_obj._get_report_from_name(
            "ec_electronic_billing.report_invoice"
        )
        custom_data = self.env["model.name"].get_data()

        docargs = {
            "doc_ids": docids,
            "doc_model": report.model,
            "docs": self,
            "custom_data": custom_data,
        }
        return report_obj.render("ec_electronic_billing.report_invoice", docargs)
