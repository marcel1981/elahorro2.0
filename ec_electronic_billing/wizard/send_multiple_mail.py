from odoo import models, api
import logging
import pdb

class generate_ean_wizard(models.TransientModel):
    _name = 'send.mail.wizard'
    _description = 'Send multiples mail.'
    logger = logging.getLogger('wizard.send.mail')

    @api.multi
    def send_mail(self):
        invoice_obj = self.env['account.invoice']
        ctx = self._context or {}
        model = ctx.get('active_model')
        if model == 'account.invoice':
            self.logger.info("sending mail to client")
            invoice_ids = ctx.get('active_ids', [])
            invoices = invoice_obj.search([('id', 'in', invoice_ids)])
            for invoice in invoices:
                self.logger.info("sending mail to client")
                if invoice.sri_response == '3':
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
