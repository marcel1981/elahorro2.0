# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from . import utils_id

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):

    _inherit = "res.partner"
    identification = fields.Char("Cédula/RUC", size=13, help="Identificación")

    type_identifier = fields.Selection(
        [
            ("04", "RUC"),
            ("05", "CEDULA"),
            ("06", "PASAPORTE"),
            ("07", "CONSUMIDOR FINAL"),
        ],
        string="Tipo ID",
        default="06",
        required=True,
    )

    @api.constrains("identification", "type_identifier")
    def _ci_unique(self):
        for record in self:
            if record.identification and record.type_identifier:
                ci_ruc = utils_id.Identifier()
                if record.type_identifier == "04" or record.type_identifier == "05":
                    if not ci_ruc.validate_ci_ruc(
                        record.identification, record.type_identifier
                    ):
                        raise ValidationError("Identificacion Erróneo")
                if record.type_identifier == "07":
                    if record.identification != "9999999999999":
                        raise ValidationError("Identificacion Erróneo")
                partner = self.env["res.partner"].search(
                    [
                        ("identification", "=", record.identification),
                        ("id", "!=", record.id),
                    ]
                )

                if len(partner) > 0:
                    raise ValidationError("El c.i debe ser único")

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        try:
            recs = self.search(
                [
                    "|",
                    "|",
                    ("identification", operator, name),
                    ("name", operator, name),
                    ("vat", operator, name),
                ]
                + args,
                limit=limit,
            )
        except:
            recs = self.search(
                ["|", ("identification", operator, name), ("name", operator, name)]
                + args,
                limit=limit,
            )
        return recs.name_get()

    # def is_email(self):
    #    if self.email:
    #        if not re.match('^[(a-z0-9\_\-\.)]+@[(a-z0-9\_\-\.)]+\.[(a-z)]{2,15}$', self.email):
    #           raise ValidationError('Email incorrecto')
