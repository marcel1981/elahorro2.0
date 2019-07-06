from odoo import api, fields, models


class DocoumentElectronic(models.Model):
    _inherit = 'document.electronic'


    def _detalles(self):
        res = super(DocoumentElectronic, self)._detalles()
        res.update({
            'Descuento': sum([
                res['detalles'].remove(det) or float(det.get('precioUnitario')) * float(det.get('cantidad'))
                for det in res.get('detalles') if float(det.get('cantidad')) < 1
            ])
        })
        return res