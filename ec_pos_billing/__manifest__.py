# -*- coding: utf-8 -*-
{
    'name': "ec_pos_billing",

    'summary': """
        Facturación Electrónica """,

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
    'depends': ['base', 'point_of_sale', 'mail', 'contacts', 'ec_partner',
                'ec_electronic_billing'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/cron_order.xml',
        'views/pos.xml',
        'views/pos_dte.xml',
        'views/pos_session.xml',
        'views/pos_default_partner.xml',
        'views/order.xml',
        'email/email_client.xml',
    ],
    'qweb': [
        'static/src/xml/client.xml',
        'static/src/xml/pos.xml',
        'static/src/xml/receipt.xml',
    ],
    # only loaded in demonstration mode
    "application": True,
}