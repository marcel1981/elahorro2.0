#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockRotationReport(models.TransientModel):
    _name = "wizard.stock.rotation.report"

    warehouse_ids = fields.Many2many("stock.warehouse", string=_("Warehouses"))
    category_ids = fields.Many2many("product.category", string=_("Product Category"))
    product_ids = fields.Many2many("product.product", string=_("Products"))
    from_date = fields.Date(string=_("From Date"), required=True)
    to_date = fields.Date(string=_("To Date"), required=True)
    consolidated = fields.Boolean(
        string=_("Consolidated"),
        default=False,
        help=_(
            "Check this box if you wish to obtain additional consolidated information from the report."
        ),
    )

    @api.onchange("category_ids")
    def _onchange_categ_id(self):
        res = {"values": {}, "domain": {}}
        categ_ids = []
        if self.category_ids:
            categ_ids = self.category_ids.ids
            res["domain"] = {"product_ids": [("categ_id", "in", categ_ids)]}
        return res

    @api.multi
    def print_report(self):
        context = self._context
        datas = {"ids": context.get("active_ids", [])}
        datas["model"] = "wizard.stock.rotation.report"
        datas["form"] = self.read()[0]
        for field in datas["form"].keys():
            if isinstance(datas["form"][field], tuple):
                datas["form"][field] = datas["form"][field][0]
        location_obj = self.env["stock.location"]
        for row in self:
            warehouse_ids = row.mapped("warehouse_ids") or row.warehouse_ids.search([])
            locations = (
                row.mapped("warehouse_ids")
                .search([("id", "in", warehouse_ids.ids)])
                .mapped("lot_stock_id")
                .mapped("location_id")
                .ids
            )
            domain = [("location_id", "in", locations)]
            category_ids = row.mapped("category_ids") or row.category_ids.search([])
            location_ids = location_obj.search(domain)
            product_ids = (
                row.mapped("product_ids")
                or self.env["product.product"]
                .search([("categ_id", "in", category_ids.ids)])
                .ids
            )
        if not location_ids:
            raise ValidationError(
                _(
                    "The Warehouses {} has no {} locations".format(
                        ",".join(map(str, warehouse_ids.mapped("name"))),
                        dict(self._fields["location_usage"].selection).get(
                            row.location_usage
                        ),
                    )
                )
            )
        if not product_ids:
            raise ValidationError(
                _(
                    "There are no products with it for the selected categories {}".format(
                        ",".join(map(str, row.category_ids.mapped("name")))
                    )
                )
            )
        return self.env.ref(
            "stock_base_reports.stock_inventory_rotation"
        ).report_action(self, data=datas)
