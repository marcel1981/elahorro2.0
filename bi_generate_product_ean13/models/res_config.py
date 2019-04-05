# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from openerp import fields, models, api, _


class SaleConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    gen_barcode = fields.Boolean("Geneación de código EAN13 en el Producto")
    generate_option = fields.Selection([('date', 'Generar código de barras EAN13 (Usando la fecha actual)'),
                                        ('random', 'Generar código de barras EAN13 (Usando un número randómico)')],string='Opciones de generar código de barras',default='date')

    @api.model
    def default_get(self, fields_list):
        res = super(SaleConfigSettings, self).default_get(fields_list)
        if self.search([], limit=1, order="id desc").gen_barcode == 1:
            gen_opt = self.search([], limit=1, order="id desc").generate_option
            res.update({'gen_barcode': 1,
                        'generate_option':gen_opt})
            
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
