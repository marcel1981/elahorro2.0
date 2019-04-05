import logging
from datetime import datetime
from odoo import models, api
from . import utils
import pdb

class Order(models.Model):
    _name = 'order.invoice'
    _inherit = ('pos.order')
    _logger = logging.getLogger('cron.order.pos')

    @api.model
    def cron_do(self):
        self._logger.info("Order to invoice...")

        orders = self.env['pos.order'].search([("invoice_id", "=", False)])
        for o in orders:
            if not o.invoice_id:
                o.posOrderInvoice()

        orders = self.env['pos.order'].search(['|','|', ("sri_response", "=", "1"), ("sri_response", "=", "5"), ("sri_response", "=", "6")])

        if orders:
            api = '{}{}'.format(self._get_acive_api_sri(orders[1].company_id), '/RecepcionComprobantesOffline?wsdl')
            if not utils.checkService(api):
                self._logger.info("Servicio no disponible SRI")
                return False

            for order in orders:
                #pdb.set_trace()
                if order.state == 'paid' or order.state == 'invoiced' or order.state == 'done':
                    if not order.state == 'invoiced':
                        order.posOrderInvoice()
                    if order.invoice_id.sri_response == '1' or order.invoice_id.sri_response == '5':
                        if order.amount_total > 0:
                            order.action_send_invoice()
                            self.env.cr.commit()
        self._logger.info("Finaly Order to invoice...")
