# -*- coding: utf-8 -*-
{
    'name': "ec_pos_ajust",
    'summary': """
        Short fixes modules
    """,
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'pos',
    'version': '0.1',
    'depends': [
        'ec_pos_billing',
        'aspl_pos_promotion',
        'ec_11_pos_seller'
    ],
    'data': [
        'views/views.xml',
        'views/pos_promotion_view.xml',
        'views/promotion_templates.xml',
    ],
    'qweb': [
        'static/src/xml/receipt.xml',
    ],
}