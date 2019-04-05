# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import pdb

class pos_order(models.Model):
    _inherit = "pos.order"
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        pos_ids = []
        if self.env.user.is_cashier:
            #pdb.set_trace()
            if len(args) == 0:
                limit = 1


        if self.env.user.wise_config:
            posAsiggned = self.env.user.config_pos
            if posAsiggned:
                for pos in posAsiggned:
                    pos_ids.append(pos.id)

            if pos_ids:
                if not args:
                    args = [('config_id', 'in', pos_ids)]
                else:
                    args.append(('config_id', 'in', pos_ids))
        return super(pos_order, self).search(args, offset=offset, limit=limit, order=order, count=count)
