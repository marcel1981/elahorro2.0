# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import Warning
from odoo import models, fields, api, _



class ProductSettingSku(models.Model):
    _name = "product.setting.sku"

    name = fields.Char('Name', required=True)
    product = fields.Selection([('two','First Two Digit'),('three','First Three Digit'),('four','First Four Digit')],default="two", string="Product Variant")
    attribute = fields.Selection([('two','First Two Letters'),('three','First Three Letters'),('four','First Four Letters')],default="two", string="Attribute")
    category = fields.Selection(
        [('two', 'First Two Letters'), ('three', 'First Three Letters'), ('four', 'First Four Letters')], default="two",
        string="Category")
    use_attribute = fields.Boolean('Use Attribute')
    use_category = fields.Boolean('Use Category')
    hyphens_opt = fields.Boolean('Use hyphens')
    pattern = fields.Selection([('1','0'),('2','00'),('3','000'),('4','0000'),
    ('5', '00000'),('6','000000'),('7','0000000'),('8','00000000'),
    ('9', '000000000'),('10','0000000000')], string="Pattern With Database Id")


    @api.model
    def default_get(self, fields):
        config_id = self.search([], limit=1, order="id desc")
        res = super(ProductSettingSku, self).default_get(fields)
        if config_id:
            res.update(
                {
                    'name': config_id.name,
                    'product': config_id.product,
                    'attribute': config_id.attribute,
                    'hyphens_opt': config_id.hyphens_opt,
                    'category':config_id.category,
                    'use_attribute':config_id.use_attribute,
                    'use_category':config_id.use_category,
                    'pattern':config_id.pattern


                }
            )
        return res
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    



