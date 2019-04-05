# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)


class AccountJournal(models.Model):

    _inherit = 'account.journal'
    isJournalCreditNote = fields.Boolean("Diario Nota de Crédito", required=False)
    isJournalRetention = fields.Boolean("Diario Retenciones", required=False)