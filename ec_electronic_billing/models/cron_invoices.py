import logging
from odoo import models, api
import pdb


class CronInvoice(models.Model):
    _name = 'cron.invoice'
    _inherit = ('account.invoice')

    types = {
        'out_invoice': 'invoice',
        'out_refund': 'note_credit',
    }

    @api.model
    def cron_do(self):
        self._logger.info("Send Invoices")
        invoices = self.env['account.invoice'].search(['|', ("sri_response", "=", "1"), ("sri_response", "=", "5")])
        for invoice in invoices:
            logging.info("Invoice Number {}".format(invoice))
            if invoice.state == 'paid':
                if not invoice.physical_billing:
                    invoice.action_send_invoice()
                    self.env.cr.commit()