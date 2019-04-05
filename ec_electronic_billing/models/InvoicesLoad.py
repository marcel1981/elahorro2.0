# -*- coding: utf-8 -*-
import os
import logging
import base64
import csv
from odoo import models, fields, api


class AccountInvoice(models.Model):
    _name = 'load.invoice'
    fileInvoice = fields.Binary('Certificado Firma electrónica')

    @api.multi
    def loadInvoices(self):
        filecontent = base64.b64decode(self.fileInvoice)
        #logging.info(filecontent)
        #logging.info(filecontent)
        reader = csv.reader(str(filecontent[0]).split("\n"))

        #filecontent = base64.b64decode(self.file_electronic_signature)
        #logging.info(filecontent)
        numInvoice = 0
        for line in filecontent.decode("utf-8").split("\n"):
            values = line.split(',')
            if values[0]:
                invoice = self.env['account.invoice'].search([("id", "=",values[0])])
                if invoice:
                    logging.info(invoice)
                    if invoice.identification == values[1]:
                        numInvoice += 1
                        logging.info(numInvoice)
                        invoice.access_key = values[2]
                        invoice.write({'access_key': values[2]})

