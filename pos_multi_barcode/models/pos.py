# -*- coding: utf-8 -*-


from odoo import fields, models,tools,api

class pos_multi_barcode(models.Model):
    _name = 'pos.multi.barcode'

    name = fields.Char('Barcode')
    product_id = fields.Many2one("product.product",string="Product")


class product_product(models.Model):
    _inherit = 'product.product'

    pos_multi_barcode = fields.One2many('pos.multi.barcode','product_id',string='Barcodes')




    