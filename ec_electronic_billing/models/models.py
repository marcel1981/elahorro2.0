# -*- coding: utf-8 -*-

from odoo import models, fields, api

class product(models.Model):
    _inherit = "product.product"

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        limit = 1000
        return super(product, self).search(args, offset=offset, limit=limit, order=order, count=count)


class productTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        limit = 1000
        return super(productTemplate, self).search(args, offset=offset, limit=limit, order=order, count=count)