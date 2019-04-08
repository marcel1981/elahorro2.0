# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
import base64
import logging
import os
import random
from datetime import datetime

from io import BytesIO

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

try:
    from barcode import generate
    from barcode.writer import ImageWriter
except ImportError:
    ImageWriter = None
    _logger.warning(
        "The module viivakoodi can't be loaded, try: pip install viivakoodi"
    )


class biproductgeneratebarcodemanually(models.TransientModel):
    _name = "bi.product.generate.barcode.manually"

    generate_type = fields.Selection(
        [
            ("date", "Generación de código de barras EAN13 (Usando fecha actual)"),
            (
                "random",
                "Generación de código de barras EAN13 (Usando´numeros randómicos)",
            ),
        ],
        string="Opciones de generar código de barras",
        default="date",
    )

    @api.multi
    def generate_barcode_manually(self):
        for record in self.env["product.product"].browse(
            self._context.get("active_id")
        ):
            if self.generate_type == "date":
                bcode = self.env["barcode.nomenclature"].sanitize_ean(
                    "%s%s" % (record.id, datetime.now().strftime("%d%m%y%H%M"))
                )
            else:
                number_random = int("%0.13d" % random.randint(0, 999999999999))
                bcode = self.env["barcode.nomenclature"].sanitize_ean(
                    "%s" % (number_random)
                )
            record.write({"barcode": bcode})
            if ImageWriter is not None:
                ean = BytesIO()
                generate("ean13", u"{}".format(bcode), writer=ImageWriter(), output=ean)
                ean.seek(0)
                jpgdata = ean.read()
                imgdata = base64.encodestring(jpgdata)
                record.write({"barcode_img": imgdata})
        return True


class bi_generate_product_barcode(models.TransientModel):
    _name = "bi.product.generate.barcode"

    overwrite = fields.Boolean(String="Overwrite Exists Ean13")
    generate_type = fields.Selection(
        [
            ("date", "Generación de código de barras EAN13 (Usando´fecha actual)"),
            (
                "random",
                "Generación de código de barras EAN13 (Usando´numeros randómicos)",
            ),
        ],
        string="Opciones de generación de código de barras",
        default="date",
    )

    @api.multi
    def generate_barcode(self):

        for record in self.env["product.product"].browse(
            self._context.get("active_ids")
        ):
            if not self.overwrite and record.barcode:
                continue

            if self.generate_type == "date":
                bcode = self.env["barcode.nomenclature"].sanitize_ean(
                    "%s%s" % (record.id, datetime.now().strftime("%d%m%y%H%M"))
                )
            else:
                number_random = int("%0.13d" % random.randint(0, 999999999999))
                bcode = self.env["barcode.nomenclature"].sanitize_ean(
                    "%s" % (number_random)
                )
            ean = BytesIO()
            generate("ean13", u"{}".format(bcode), writer=ImageWriter(), output=ean)
            ean.seek(0)
            jpgdata = ean.read()
            imgdata = base64.encodestring(jpgdata)
            record.write({"barcode": bcode, "barcode_img": imgdata})
        return True


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
