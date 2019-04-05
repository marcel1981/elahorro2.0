# -*- coding: utf-8 -*-
import os
import base64
from datetime import datetime

from odoo import models, fields, api

from OpenSSL import crypto
import logging

from odoo.exceptions import UserError, ValidationError

from . import utils_id

logger = logging.getLogger(__name__)


class Company(models.Model):
    """heredar de compañia y crear campos firma electronica"""

    _inherit = 'res.company'

    password_electronic_signature = fields.Char(string="Clave Firma", size=255)
    file_electronic_signature = fields.Binary('Certificado Firma electrónica')
    file_electronic_signature_filename = fields.Char(string='Filename')
    electronic_signature = fields.Char(string="Firma Electrónica", size=128, )
    owner_signature = fields.Char('Propietario')
    date_expirate = fields.Char('Fecha Expiración')
    state = fields.Selection([('sin_verificar', 'Sin verificar'), ('aprobado', 'Aprobado'), ('vencido', 'Vencido')],
                             default='sin_verificar',
                             string='Estado')
    # Others data
    url_test = fields.Char(string="Url ambiente de pruebas", size=255, )
    url_production = fields.Char(string="Url ambiente producción", size=255, )
    env_type = fields.Selection([('1', 'Test'), ('2', 'Production')],
                                string='Tipo de Ambiente',
                                required=True,
                                default='1')
    max_time = fields.Integer('Tiempo máximo de espera', default=3, size=10)
    # data extra company
    bill_electronic = fields.Boolean("Facturación Electrónica")
    full_name = fields.Char(string="Razón Social", size=455, )
    name_comercial = fields.Char(string="Nombre Comercial", size=455, )
    number_resolution = fields.Char(string="No. de Resolución contibruyente especial", size=455, )
    keep_accounting = fields.Selection([('SI', 'Si'), ('NO', 'No')],
                                       string='¿Obligado a llevar contabilidad?',
                                       required=True,
                                       default='NO')


    @api.one
    @api.constrains('vat', 'name')
    def is_vat(self):
        company = self
        ruc = company.vat
        if not company.vat:
            raise ValidationError('El R.U.C es obligatorio')
        if company.vat:
            validate_ruc = utils_id.Identifier()
            if not validate_ruc.validate_ci_ruc(ruc, '04'):
                raise ValidationError('R.U.C Erróneo')


    @api.onchange('file_electronic_signature')
    def onchange_file_electronic_signature(self):

        if not self.file_electronic_signature:
            self.password_electronic_signature = None
            self.owner_signature = ''
            self.date_expirate = ''
            self.state = 'sin_verificar'

    @api.multi
    def action_load_signature(self):
        """load file electronic signature"""

        filecontent = base64.b64decode(self.file_electronic_signature)
        # p = crypto.load_pkcs12(open('path', 'rb').read(), self.password_electronic_signature)
        try:
            signature = crypto.load_pkcs12(filecontent, self.password_electronic_signature)
        except:
            return False
        return signature

    @api.multi
    def action_is_valid_signature(self):
        """read signature check valid"""
        signature = self.action_load_signature()

        if signature:
            certificate = signature.get_certificate()
            private_key = signature.get_privatekey()

            if private_key.check():
                logger.info("Valid Certificate: {}".format(private_key.check()))

                self.state = 'aprobado'
                if certificate.has_expired():
                    self.state = 'vencido'

                self.owner_signature = signature.get_friendlyname()
                self.date_expirate = str(datetime.strptime(certificate.get_notAfter().decode('utf-8'), "%Y%m%d%H%M%SZ"))

    @api.multi
    def action_has_expired_signature(self, file, password):
        p = crypto.load_pkcs12(
            open(file, 'rb').read(), password)

        certificate = p.get_certificate()

        if certificate.has_expired():
            logger.info("Certificate not expired: {}".format(certificate.has_expired()))
            return True

    @api.multi
    def action_get_notAfter_signature(self, file, password):
        p = crypto.load_pkcs12(
            open(file, 'rb').read(), password)

        certificate = p.get_certificate()
        time_expired = datetime.strptime(certificate.get_notAfter().decode('utf-8'), "%Y%m%d%H%M%SZ")
        logger.info("Time for expire: {}".format(certificate.get_notAfter()))

        return time_expired

    @api.multi
    def action_signature_delete(self):

        signature = self.action_load_signature()

        if signature:
            self.state = 'sin_verificar'
            self.password_electronic_signature = ''
            self.file_electronic_signature = ''
            self.date_expirate = ''
            self.owner_signature = ''
            return True
