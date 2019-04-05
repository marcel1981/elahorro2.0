from odoo import models, api
import logging

class generate_ean_wizard(models.TransientModel):
    _name = 'send.mail.block.wizard'
    _description = 'Send multiples mail.'
    logger = logging.getLogger('wizard.send.mail')

    @api.multi
    def send_mail(self):
        invoices = self.env['account.invoice'].search([("sri_response", "=", "3")])
        for invoice in invoices:
            self.logger.info("sending mail to client")
            if invoice.sri_response == '3':
                if not invoice.send_mail_client:
                    atts = []
                    attach = invoice.create_attachment(invoice.xml_sri_request_id.sri_xml_response, 'FV#{}'.format(invoice.access_key), invoice.id)
                    atts.append(attach)
                    file_name = 'FV#{}'.format(invoice.access_key)
                    attach_pdf = invoice.create_attachment_pdf(file_name, invoice)
                    atts.append(attach_pdf)
                    send_mail = invoice.send_email(invoice, attachments=[(4, a.id) for a in atts])
                    if send_mail:
                        invoice.send_mail_client = True
        return True