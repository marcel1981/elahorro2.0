from odoo import models, fields, api
import logging
import pdb

class PosInvoice(models.Model):
    _inherit = 'pos.session'
    _logger = logging.getLogger('pos.invoice')

    
    """def action_pos_session_validate_invoice(self):
        self.actionSessionConvertOrderToInvoice()
        self._check_pos_session_balance()
        for session in self:
            session.write({'state': 'closing_control', 'stop_at': fields.Datetime.now()})
            if not session.config_id.cash_control:
                session.action_pos_session_close()"""

    def actionSessionConvertOrderToInvoice(self):
        orders = self.env['pos.order'].search([('session_id', '=', self.id)])
        for order in orders:
            if not order.state == 'invoiced':
                order.action_pos_order_invoice()
                order.invoice_id.action_invoice_open()

    @api.multi
    def action_pos_session_validate(self):
        self.actionSessionConvertOrderToInvoice()
        self._check_pos_session_balance()
        self.action_pos_session_close()
        
