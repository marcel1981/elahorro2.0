# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = "pos.order"

    pos_location_id = fields.Many2one(
        "pos.location",
        string="Ubicacion"
    )
    pos_salesman_id = fields.Many2one(
        "pos.salesman",
        string="Vendedora de Mostrador")

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        if 'vendedora_id' in ui_order.keys():
            res['pos_salesman_id'] = ui_order.get('vendedora_id')
            if res.get('session_id'):
                session_id = self.env['pos.session'].browse(res['session_id'])
                location = session_id.config_id.pos_location_id
                if location:
                    res['pos_location_id'] = location.id
        return res

    @api.multi
    def action_pos_order_invoice(self):
        """
        todo: Este mnetodo no puede ser llamado para crear multiples facturas
        Dado que no  esta preparado para operar sobre mas de un registro
        No  se ha implementado dado que el propio core de odoo en el Pos
        solo se permite crear factura de un pedido del pos de 1 factura
        :return: Factura
        """
        self.ensure_one()
        res = super(PosOrder, self).action_pos_order_invoice()
        if res.get('res_id'):
            res_id = res.get('res_id')
            invoice = self.env['account.invoice'].browse(res_id)
            if invoice:
               
                if invoice.amount_total_company_signed > 0:
                    
                    config_invoice_pos = self._config_establishment()
                    invoice.code_emission = config_invoice_pos
                    
                    access_key, emission_code = self._get_codes('invoice')

                    if not invoice.invoice_number:
                        invoice.invoice_number = "{}-{}-{}".format(
                            invoice.code_emission.number_establishment.number_establish,
                            invoice.code_emission.code_emission, self.get_secuencial())
                        self._sequence_config_establishment()
                    
                    invoice.write({
                        'pos_location_id': self.pos_location_id.id,
                        'pos_salesman_id': self.pos_salesman_id.id,
                        'access_key': access_key
                    })

                invoice.write({
                    'pos_location_id': self.pos_location_id.id,
                    'pos_salesman_id': self.pos_salesman_id.id,
                })

        return res
