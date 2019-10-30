#!/usr/bin/env python
# -*- coding: utf-8 -*-
{
    "name": "Coupon Management",
    "version": "11.0.1.0.0",
    "category": "Uncategorized",
    "summary": "Manage and pay with Coupons on Sales Orders or Point of Sale",
    "author": "",
    "website": "",
    "company": "",
    "depends": ["account_payment", "ec_partner", "point_of_sale", "sale_management"],
    "data": [
        "security/ir.model.access.csv",
        "data/journal_data.xml",
        "views/account.xml",
        "views/coupons.xml",
    ],
    "qweb": [],
    "images": [],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "auto_install": False,
}
