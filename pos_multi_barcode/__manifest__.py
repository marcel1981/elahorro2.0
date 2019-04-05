# -*- coding: utf-8 -*-

{
    'name': 'Pos Multi Barcode',
    'version': '1.0',
    'category': 'Product',
    'sequence': 6,
    'author': 'Webveer',
    'summary': "Pos multi barcode module allows you to create multiple barcode for a single product." ,
    'description': """

=======================

Pos multi barcode module allows you to create multiple barcode for a single product.

""",
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml'
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
    'images': [
        'static/description/add.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 20,
    'currency': 'EUR',
}
