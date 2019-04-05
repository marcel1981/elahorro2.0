# -*- coding: utf-8 -*-
{
    'name': "ec_11_reprint_ticket",

    'summary': """
        Reprint ticket of the Point of sale""",

    'description': """
         Reprint ticket of the Point of sale
    """,

    'author': "Ominec",
    'website': "http://ominec.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/report_reprint_ticket.xml',
        'views/report_qwe.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    "application": True,
}