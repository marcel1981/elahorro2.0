# -*- coding: utf-8 -*-
import os
from multiprocessing import TimeoutError
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import base64
import logging

from lxml import etree
from lxml.etree import fromstring, DocumentInvalid

try:
    from suds.client import Client
except ImportError:
    raise ImportError('Instalar Libreria suds: pip install suds-jurko')

import pdb

from .xades import CheckDigit

SCHEMAS = {
    'invoice': 'schemas/factura.xsd',
    'note_credit': 'schemas/nota_credito.xsd',
    'withdrawing': 'schemas/retencion.xsd',
    'delivery': 'schemas/guia_remision.xsd',
    'in_refund': 'schemas/nota_debito.xsd',
    'retention': 'schemas/retencion.xsd'
}

class DocumentXML(object):
    _schema = False
    document = False

    @classmethod
    def __init__(self, document, type='invoice'):
        """document: XML representation type: determinate schema"""
        parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
        self.document = fromstring(document.encode('utf-8'), parser=parser)
        self.type_document = type
        self._schema = SCHEMAS[self.type_document]
        self.signed_document = False
        self.logger = logging.getLogger('xades.sri')

    @classmethod
    def validate_xml(self):
        """Validar esquema XML"""

        self.logger.info('Validacion de esquema')
        self.logger.debug(etree.tostring(self.document, pretty_print=True))
        file_path = os.path.join(os.path.dirname(__file__), self._schema)
        schema_file = open(file_path, encoding="utf-8")
        xmlschema_doc = etree.parse(schema_file)
        xmlschema = etree.XMLSchema(xmlschema_doc)
        try:
            xmlschema.assertValid(self.document)
            return True
        except DocumentInvalid:
            return False

    @classmethod
    def send_xml_sri(self, document, api_sri, timeout):
        """Metodo que envia el XML al WS"""

        self.logger.info('Enviando documento ws SRI billing')
        buf = StringIO()
        buf.write(str(document))
        buffer_xml = base64.encodestring(str(document).encode("utf-8")).decode()

        try:
            client = Client('{}{}'.format(api_sri, '/RecepcionComprobantesOffline?wsdl', timeout=timeout))
        except TimeoutError:
            return False, 'Se acabó el tiempo de espera SRI'

        try:
            result = client.service.validarComprobante(buffer_xml)
        except:
            return False, 'Error en el SRI no responde'

        self.logger.info('documento: %s' % document)
        self.logger.info('Estado de respuesta documento: %s' % result)

        errores = []
        if 'estado' in result:
            if result.estado == 'RECIBIDA':
                return True, result
            else:
                for comp in result.comprobantes:
                    for m in comp[1][0].mensajes:
                        rs = [m[1][0].tipo, m[1][0].mensaje]
                        rs.append(getattr(m[1][0], 'informacionAdicional', ''))
                        errores.append(' '.join(rs))
                self.logger.error(errores)
                return False, ', '.join(errores)
        else:
            return False, result


    def request_authorization(self, access_key, url_api):
        self.logger.info("access key  {}".format(access_key))
        self.logger.info("url  {}".format(url_api))
        messages = []
        client = Client('{}{}'.format(url_api, '/AutorizacionComprobantesOffline?wsdl'))
        try:
            result = client.service.autorizacionComprobante(access_key)
        except:
            return False, 'Autorizaciòn Error en el SRI no responde', messages
        if result:
            if 'autorizaciones' in result and result.autorizaciones:
                autorizacion = result.autorizaciones[0][0]
                mensajes = autorizacion.mensajes and autorizacion.mensajes[0] or []
                self.logger.info('Estado de autorizacion {}'.format(autorizacion.estado))
                for m in mensajes:
                    messages.append([m])
                if not autorizacion.estado == 'AUTORIZADO':
                    return False, result, messages
                return True, autorizacion.comprobante, autorizacion
        return False, result, messages

class SriService(object):

    @classmethod
    def create_access_key(self, values):
        """ access ey 48 digits sri"""
        dato = ''.join(values[0] + values[1])
        modulo = CheckDigit.compute_mod11(dato)
        access_key = ''.join([dato, str(modulo)])
        return access_key
