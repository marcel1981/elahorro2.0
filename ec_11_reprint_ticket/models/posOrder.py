# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

import logging

_logger = logging.getLogger(__name__)


class POS(models.Model):
    _inherit = 'pos.order'

    @api.multi
    def printTicket(self):
        """ Print NC
        """
        return self.env.ref('ec_11_reprint_ticket.action_print_ticket').report_action(self)
    