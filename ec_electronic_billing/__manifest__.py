# -*- coding: utf-8 -*-
{
    'name': "ec_electronic_billing",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'account',
                'account_invoicing',
                'sale_management',
                'hr',
                'web'
                ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/ir.model.access.csv',
        'views/invoice.xml',
        'views/config_einvoice.xml',
        'views/company.xml',
        'views/invoice_qwe.xml',
        'views/credit_note_qwe.xml',
        'views/retentionQwe.xml',
        'views/establishment.xml',
        'views/point_emission.xml',
        'wizard/send_multiple_mail.xml',
        'views/cron_auth.xml',
        'views/cron_invoices.xml',
        'views/accountJournal.xml',
        'views/accountTax.xml',
        'views/retention.xml',
        'views/report_invoice.xml',
        'views/report_credit_note.xml',
        'views/reportRetention.xml',
        'views/loadInvoices.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    "application": True,
}