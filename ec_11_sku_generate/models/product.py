# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import Warning
from odoo import models, fields, api, _


class Product(models.Model):
    _inherit = "product.template"

    @api.one
    def _make_sku_sequence(self):

        config_id = self.env['product.setting.sku'].search([], limit=1, order="id desc")
        product_template = self.pool.get('product.template')

        product = self
        string = ''
        temp = ''
        if config_id.product == 'two':
            count = 2
        elif config_id.product == 'three':
            count = 3
        elif config_id.product == 'four':
            count = 4
        else:
            raise Warning('Please Select Correct One')
        string+=product.name[0:count] + "-"
        if config_id.use_attribute:
            if product.attribute_line_ids:
                for att_line in product.attribute_line_ids:
                    for att in att_line.value_ids:
                        if config_id.attribute == 'two':
                            count = 2
                        elif config_id.attribute == 'three':
                            count = 3
                        elif config_id.attribute == 'four':
                            count = 4
                        else:
                            raise Warning('Please Select Correct One')

                        string+=att.name[0:count] + "-"
        if config_id.use_category:
            if config_id.category == 'two':
                count = 2
            elif config_id.category == 'three':
                count = 3
            elif config_id.category == 'four':
                count = 4
            else:
                raise Warning('Please Select Correct One')

            string += product.categ_id.name[0:count] + "-"
        for a in range(int(float(config_id.pattern))):
            temp += "0"
        string += temp + str(product.id)

        if not config_id.hyphens_opt:
            string = str(string)
            string = string.replace('-', '')
        if string:
            product.default_code1 = string
            #product.default_code = string
        self.write({'default_code': string})
    default_code1 = fields.Char('Referencia Interna Variantes', compute='_make_sku_sequence')


class Product(models.Model):
    _inherit = "product.product"

    @api.one
    def _make_sku_sequence(self):

        config_id = self.env['product.setting.sku'].search([], limit=1, order="id desc")
        if not config_id:
            return
        product = self
        string = ''
        temp = ''
        if config_id.product == 'two':
            count = 2
        elif config_id.product == 'three':
            count = 3
        elif config_id.product == 'four':
            count = 4
        else:
            raise Warning('Please Select Correct One')
        string+=product.name[0:count] + "-"
        if config_id.use_attribute:
            if product.attribute_value_ids:
                for att in product.attribute_value_ids:
                    if config_id.attribute == 'two':
                        count = 2
                    elif config_id.attribute == 'three':
                        count = 3
                    elif config_id.attribute == 'four':
                        count = 4
                    else:
                        raise Warning('Please Select Correct One')

                    string+=att.name[0:count] + "-"
        if config_id.use_category:
            if config_id.category == 'two':
                count = 2
            elif config_id.category == 'three':
                count = 3
            elif config_id.category == 'four':
                count = 4
            else:
                raise Warning('Please Select Correct One')

            string += product.categ_id.name[0:count] + "-"
        for a in range(int(float(config_id.pattern))):
            temp += "0"
        string += temp + str(product.id)

        if not config_id.hyphens_opt:
            string = str(string)
            string = string.replace('-', '')
        if string:
            product.default_code1 = string
            #product.default_code = string
        self.write({'default_code': string})

    default_code1 = fields.Char('Referencia Interna Variantes', compute='_make_sku_sequence')



