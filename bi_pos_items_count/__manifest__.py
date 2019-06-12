# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
	"name" : "POS Item Total(Count) in odoo",
	"version" : "11.0.0.1",
	"category" : "Point of Sale",
	'summary': 'This apps helps to show total number of quantity in POS screen and receipt',
	"description": """
	
		Purpose :-
		This apps helps to show total number of quantity in POS screen and receipt
		POS item count, POS items count
		POS count item
		POS Item Total, pos item number , pos item no , 
		POS total items
		POS item-count
		pos number of item
		pos total no of item
		pos product qty total
		pos product total
		pos quantity total
		pos total quantity

		Point of Sale item count, Point of Sale items count
		Point of Sale count item
		Point of Sale Item Total
		Point of Sale total items
		Point of Sale item-count
		Point of Sale number of item
		Point of Sale total no of item
		Point of Sale product qty total
		Point of Sale product total
		Point of Sale quantity total
		Point of Sale total quantity

		total number of quantity on pos screen
		total number of quantity on pos receipt
		pos total number of quantity
		pos recipt total number of quantity
		pos product total number of quantity
		pos receipt product total number of quantity
		pos number of product on screen 
		pos number of product on receipt

		total number of quantity on point of sale screen
		total number of quantity on point of sale receipt
		point of sale total number of quantity
		point of sale recipt total number of quantity
		point of sale product total number of quantity
		point of sale receipt product total number of quantity
		point of sale number of product on screen 
		point of sale number of product on receipt
	
	""",
	"author": "BrowseInfo",
	"website" : "www.browseinfo.in",
	"price": 10,
	"currency": 'EUR',
	"depends" : ['base','sale','point_of_sale'],
	"data": [
		'views/custom_pos_view.xml',
	],
	'qweb': [
		'static/src/xml/pos.xml',
	],
	"auto_install": False,
	"installable": True,
	"live_test_url":'https://youtu.be/FKsKPz93_BY',
	"images":['static/description/Banner.png'],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
