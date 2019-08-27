import logging
from datetime import timedelta
from functools import partial

import psycopg2
import pytz

from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def create_from_ui(self, orders):
        history = self.env['pos.promotion.history'].sudo()
        [history.create({
            'promotion_id': promotion['promotion_id'],
            'partner_id': o['data']['partner_id'],
            'seq': promotion['seq'],
            'date': o['data']['creation_date']
        }) for o in orders if o['data'].get('promotion_list')
           for promotion in o['data'].get('promotion_list')]
        return super(PosOrder, self).create_from_ui(orders)
