# -*- coding: utf-8 -*-
# Licence LGPL version 3
{
    'name': "Ominec Vendedoras de Mostrador",

    'summary': """
        Gestión de vendedoras de mostrador
        """,

    'description': """
        Gestión de vendedoras de mostrador
    """,

    'author': "Ominec",
    'website': "http://ominec.com",
    'category': 'POS',
    'version': '11.0.1.1',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale', 'account'],

    # always loaded
    'data': [
        'views/pos_salesman_view.xml',
        'views/pos_location_view.xml',
        'views/pos_ominec_templates.xml',
        'views/pos_config_view.xml',
        'views/pos_order_view.xml',
        'views/account_invoice_view.xml',
        'security/ir.model.access.csv',
    ],
    'application': True,
    'qweb': ['static/src/xml/pos_templates.xml'],
}
