import os
from datetime import datetime

from jinja2 import Environment, FileSystemLoader
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

from ..sri.sri import DocumentXML, SriService
from ..sri.xades import Xades

from dateutil import tz


class PosInvoice(models.Model):
    """Model config point of sale"""

    _name = "pos.config"
    _inherit = "pos.config"
    _logger = logging.getLogger("pos.invoice")
    default_partner_id = fields.Many2one("res.partner", "Default Partner")
    establishment = fields.Many2one(
        string="Establecimiento", related="point_of_sale.number_establishment"
    )
    point_of_sale = fields.One2many("invoice.point.emission", "point_of_sale")


class PosOrder(models.Model):
    """Model Pos order proccess data invoice"""

    _name = "pos.order"
    _inherit = ("pos.order", "invoice.document")

    TEMPLATES = {"invoice": "invoice.xml", "credit_note": "credit_note.xml"}

    @api.multi
    @api.depends("date_order")
    def _get_local_datetime(self):
        tz_format = "%Y-%m-%d %H:%M:%S"
        from_zone = tz.gettz("UTC")
        to_zone = tz.gettz("America/Guayaquil")
        for row in self:
            utc = datetime.strptime(row.date_order, tz_format)
            utc = utc.replace(tzinfo=from_zone)
            row.date_order_local = utc.astimezone(to_zone).strftime(tz_format)

    # call object sri
    SriServiceObj = SriService()
    date_order_local = fields.Datetime(
        compute="_get_local_datetime",
        string=_("Date current action"),
        required=False,
        store=True,
    )

    sri_response = fields.Selection(
        [
            ("1", "No Enviado"),
            ("2", "Enviado realizado"),
            ("3", "Autorizado"),
            ("4", "Notificado"),
            ("5", "Enviado rechazado"),
            ("6", "No autorizado"),
            ("7", "Fact. Física"),
        ],
        string="Estado SRI",
        related="invoice_id.sri_response",
    )
    sri_response_order = fields.Selection(
        [("1", "No Enviado"), ("2", "Enviado realizado"), ("5", "Enviado rechazado")],
        default="1",
    )
    typeDoc = fields.Selection(
        [("1", "Factura"), ("2", "Nota de Crédito")],
        default="1",
        string="Tipo Documento",
        compute="setType",
        store=True,
    )

    send_mail_client = fields.Boolean(
        "Notificación correo", default=False, related="invoice_id.send_mail_client"
    )
    access_key = fields.Char("Clave de Acceso", related="invoice_id.access_key")
    xml_sri_request_id = fields.Many2one(
        "sri.xml.send", "SRI XML Request", related="invoice_id.xml_sri_request_id"
    )
    invoice_number = fields.Char(
        string="Nro. Documento", related="invoice_id.invoice_number"
    )
    identification = fields.Char(
        string="Identificación", related="partner_id.identification", readonly=True
    )

    @api.model
    def getAccessKey(self, pos_reference):
        order = self.env["pos.order"].search(
            [("pos_reference", "=", pos_reference[0])], limit=1
        )
        return order.access_key

    @api.one
    @api.depends("amount_total")
    def setType(self):
        if self.amount_total > 0:
            self.typeDoc = "1"
        else:
            self.typeDoc = "2"

    def _config_establishment(self):
        """Return configuration of establishment"""
        config = self.env["invoice.point.emission"].search(
            [("point_of_sale", "=", self.config_id.id)]
        )
        return config

    def _sequence_config_establishment(self):
        """refresh sequence configuration of establishment"""
        config = self.env["invoice.point.emission"].search(
            [("point_of_sale", "=", self.config_id.id)]
        )
        config.current_number_invoice += 1

    def render_document(self, order, type_doc):
        """Fill xml with the order"""
        # load xlm dir templates
        tmpl_path = os.path.join(os.path.dirname(__file__), "templates")
        env = Environment(loader=FileSystemLoader(tmpl_path))
        invoice_tmpl = env.get_template(self.TEMPLATES[type_doc])
        data = {}
        # load data pos
        data.update(self._info_tributaria(type_doc))
        data.update(self._info_factura(order))
        details = self._detalles()
        data.update(details)
        invoice = invoice_tmpl.render(data)
        return invoice

    def _get_acive_api_sri(self, company):
        """Get ws sri test o prodcution"""
        if company.env_type == "1":
            return company.url_test
        else:
            return company.url_production

    @api.one
    def posOrderInvoice(self):

        Invoice = self.env["account.invoice"]

        for order in self:
            # Force company for all SUPERUSER_ID action
            local_context = dict(
                self.env.context,
                force_company=order.company_id.id,
                company_id=order.company_id.id,
            )
            if order.invoice_id:
                Invoice += order.invoice_id
                continue

            if not order.partner_id:
                raise UserError(_("Please provide a partner for the sale."))

            invoice = Invoice.new(order._prepare_invoice())
            invoice._onchange_partner_id()
            invoice.fiscal_position_id = order.fiscal_position_id

            inv = invoice._convert_to_write(
                {name: invoice[name] for name in invoice._cache}
            )
            new_invoice = Invoice.with_context(local_context).sudo().create(inv)
            message = _(
                "This invoice has been created from the point of sale session: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>"
            ) % (order.id, order.name)
            new_invoice.message_post(body=message)
            order.write({"invoice_id": new_invoice.id, "state": "invoiced"})
            Invoice += new_invoice

            for line in order.lines:
                self.with_context(local_context)._action_create_invoice_line(
                    line, new_invoice.id
                )

            new_invoice.with_context(local_context).sudo().compute_taxes()
            order.sudo().write({"state": "invoiced"})
            order.invoice_id.action_invoice_open()
            config_invoice_pos = order._config_establishment()
            order.invoice_id.code_emission = config_invoice_pos
            order.invoice_id.date_invoice = order.date_order_local
            order.invoice_id.date_due = order.date_order_local
            order.invoice_id.date_order_local = order.date_order_local

            order.invoice_id.pos_location_id = order.pos_location_id
            order.invoice_id.pos_salesman_id = order.pos_salesman_id
            order.invoice_id.team_id = order.config_id.crm_team_id

        if not Invoice:
            return {}

        return {
            "name": _("Customer Invoice"),
            "view_type": "form",
            "view_mode": "form",
            "view_id": self.env.ref("account.invoice_form").id,
            "res_model": "account.invoice",
            "context": "{'type':'out_invoice'}",
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "target": "current",
            "res_id": Invoice and Invoice.ids[0] or False,
        }

    @api.one
    def send_email(self, attachments=[]):
        self._logger.info("Send invoice by mail ")
        template = self.env.ref("ec_pos_billing.email_template_invoice")
        if template:
            et_pool = self.pool.get("mail.template")
            mail_sent = et_pool.send_mail(
                self.env.cr,
                1,
                template.id,
                self.env.user.id,
                context={"attachment_ids": attachments},
            )
        return True

    @api.one
    def action_send_invoice(self):
        """Enviar factura electronica al SRI"""
        for order in self:
            if not order._config_establishment():
                return False
            # render xml

            invoice = self.render_document(order, "invoice")
            # valiadate xml
            inv_xml = DocumentXML(invoice, "invoice")
            inv_xml.validate_xml()
            # signarture xml
            xades = Xades()
            file_pk12 = order.company_id.file_electronic_signature
            password = order.company_id.password_electronic_signature
            signed_document = xades.sign(invoice, file_pk12, password)
            # get env company
            api_sri = self._get_acive_api_sri(order.company_id)
            timeout = order.company_id.max_time
            ok, response = inv_xml.send_xml_sri(signed_document, api_sri, timeout)
            if not self.invoice_id:
                self.sudo().posOrderInvoice()
            if self.invoice_id.sri_response == "2":
                logging.warning("La factura ya fue enviada al SRI")
                return False
            invoice = self.invoice_id

            if order.access_key:
                access_key = order.access_key
            else:
                access_key, emission_code = self._get_codes("invoice")

            self._logger.info("access key {}".format(access_key))
            config_invoice_pos = self._config_establishment()
            invoice.code_emission = config_invoice_pos
            invoice.access_key = access_key

            if not invoice.invoice_number:
                invoice.invoice_number = "{}-{}-{}".format(
                    invoice.code_emission.number_establishment.number_establish,
                    invoice.code_emission.code_emission,
                    self.get_secuencial(),
                )

                self._sequence_config_establishment()
            sri_xml = self.sudo().create_envio(response, signed_document)
            invoice.xml_sri_request_id = sri_xml

            invoice.pos_location_id = self.pos_location_id
            invoice.pos_salesman_id = self.pos_salesman_id
            invoice.team_id = self.config_id.crm_team_id

            if not ok:
                self._logger.info("Errores {}".format(response))
                self.write({"sri_response_order": "5"})
                self.invoice_id.write({"sri_response": "5"})
                return False
            self.write({"sri_response_order": "2"})
            self.invoice_id.write({"sri_response": "2"})
            return True

    @api.one
    def sendInvoiceAuthorization(self):
        if self.sri_response in ["1", "5", "6"]:
            self.action_send_invoice()

        if self.invoice_id.sri_response in ["2", "5"]:
            self.invoice_id.sendAuthorization()

    def create_envio(self, menssage, res):
        envio = {"sri_receipt": menssage, "sri_xml_response": res}
        envio_id = self.env["sri.xml.send"].sudo().create(envio)
        return envio_id
