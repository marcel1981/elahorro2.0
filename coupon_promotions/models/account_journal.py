from odoo import _, api, fields, models

class AccountJournal(models.Model):
    _inherit = "account.journal"

    iscoupon = fields.Boolean('Es Cupon?')