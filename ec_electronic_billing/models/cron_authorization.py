import logging
from odoo import models, api
from ..sri.sri import DocumentXML
import pdb


class Authorization(models.Model):
    _name = 'invoice.authorization'
    _inherit = 'account.invoice'
    _logger = logging.getLogger('invoice.authorization')

    @api.model
    def cron_do(self):
        invoices = self.env['account.invoice'].search(['|','|',("sri_response", "=", "2"), ("sri_response", "=", "5"), ("sri_response", "=", "6")])

        for invoice in invoices:
            access_key = invoice.access_key
            self._logger.info("Sending invoice to SRI {}".format(access_key))
            if access_key:
                # TODO delete static url

                if self.sri_response in ['5']:
                    self.checkIfExistCreditNoteResource()
                    self.action_send_invoice()

                api_sri = self._get_acive_api_sri(invoice.company_id)
                document = DocumentXML('doc', 'invoice')
                state, auth_xml, sms = document.request_authorization(access_key, api_sri)

                if not state:
                    invoice.sri_response = '6'
                    self._logger.warning('{}'.format('Error en la autorizaciòn al SRI'))
                    invoice.xml_sri_request_id.sri_auth = sms
                    continue
                type_document = invoice.type_document()
                if not invoice.send_mail_client:
                    atts = []
                    file_name = 'FV#{}'.format(invoice.access_key)
                    attach_xml = self.create_attachment(auth_xml, file_name, invoice.id)
                    atts.append(attach_xml)
                    attach_pdf = self.create_attachment_pdf(file_name, invoice)
                    atts.append(attach_pdf)
                    send_mail = self.send_email(invoice, attachments=[(4, a.id) for a in atts])
                    if send_mail:
                        invoice.send_mail_client = True

                self._logger.info("Number Invoice {}".format(invoice.number))
                if invoice.xml_sri_request_id:
                    invoice.xml_sri_request_id.sri_xml_response = auth_xml
                    invoice.xml_sri_request_id.sri_auth = sms
                invoice.sri_response = '3'
                self.env.cr.commit()
