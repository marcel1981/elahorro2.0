from odoo import models, http
from odoo.http import request
from odoo.addons.web.controllers.main import serialize_exception, content_disposition

class Binary(http.Controller):

    def document(self, filename, filecontent):
        if not filecontent:
            return request.not_found()
        headers = [
            ('Content-Type', 'application/xml'),
            ('Content-Disposition', content_disposition(filename)),
            ('charset', 'utf-8'),
        ]
        return request.make_response(
                filecontent, headers=headers, cookies=None)

    @http.route(["/download/xml/invoice/<model('account.invoice'):document_id>"], type='http', auth='user')
    @serialize_exception
    def download_document(self, document_id, **post):
        filename = ('FV#%s.xml' % document_id.access_key)
        filecontent = document_id.xml_sri_request_id.sri_xml_response
        return self.document(filename, filecontent)