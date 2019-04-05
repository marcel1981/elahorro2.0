# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import pdb

class pos_config(models.Model):
    _inherit = "pos.config"

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        posAsiggned = self.env.user.config_pos
        pos_ids = []
        if self.env.user.wise_config:
            if posAsiggned:
                for pos in posAsiggned:
                    pos_ids.append(pos.id)

                if pos_ids:
                    if not args:
                        args = [('id', 'in', pos_ids)]
                    else:
                        args.append(('id', 'in', pos_ids))
        return super(pos_config, self).search(args, offset=offset, limit=limit, order=order, count=count)
