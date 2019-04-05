
from odoo import models, fields, api

class SRIXMLEnvio(models.Model):
    _description = "Detalles Firma"
    _name = 'sri.xml.send'
    sri_receipt = fields.Text(string='SRI Mensaje de recepción', copy=False, readonly=True)
    sri_auth = fields.Text(string='SRI Mensaje de autorización', copy=False, readonly=True,
                           default="Aún no se ha enviado para su autorización")
    sri_xml_response = fields.Text(string='SRI XML Request', required=True)