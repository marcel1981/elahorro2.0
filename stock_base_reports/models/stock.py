#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.tools import drop_view_if_exists


class StockBase(models.Model):
    _name = "stock.base"
    _auto = False
    _rec_name = "id"

    location_id = fields.Many2one("stock.location", string=_("Location"))
    default_code = fields.Char(_("Default Code"))
    product_id = fields.Many2one("product.product", string=_("Product"))
    name = fields.Char(_("Name"))
    uom_id = fields.Many2one("product.uom", string=_("UoM"))
    product_qty = fields.Float(_("Product QTY"))
    price_unit = fields.Float(_("Price Unit"))
    date = fields.Datetime(_("Date"))
    location_org_id = fields.Many2one("stock.location", string=_("Origin Location"))
    location_dest_id = fields.Many2one(
        "stock.location", string=_("Destination Location")
    )
    type = fields.Selection(
        [
            ("inventory", _("Inventory")),
            ("sale", _("Sale")),
            ("purchase", _("Purchase")),
            ("scrap", _("Scrap")),
            ("internal", _("Internal")),
        ],
        string=_("Move Type"),
    )
    picking_id = fields.Many2one("stock.picking", string=_("Picking"))
    company_id = fields.Many2one("res.company", string=_("Company"))

    @api.model_cr
    def init(self):
        drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            """
            CREATE VIEW {} AS (
              SELECT
                i.id AS id,
                l.id AS location_id,
                pp.default_code,
                product_id,
                i.name,
                CASE
                  WHEN state = 'done' THEN  product_qty
                  ELSE 0
                END AS product_qty,
                i.price_unit,
                i.product_uom AS uom_id,
                date AT TIME ZONE 'UTC-5' AS date,
                i.location_id AS location_org_id,
                i.location_dest_id,
                CASE
                  WHEN i.inventory_id IS NOT NULL THEN 'inventory'
                  WHEN (SELECT sl.usage FROM stock_location sl WHERE sl.id = i.location_id) = 'supplier' THEN 'purchase'
                  WHEN (SELECT sl.usage FROM stock_location sl WHERE sl.id = i.location_id) = 'customer' THEN 'sale'
                  WHEN i.scrapped IS TRUE THEN 'scrap'
                  ELSE 'internal'
                END AS type,
                picking_id,
                l.company_id
              FROM
                stock_location l
                JOIN
                  stock_move i ON i.location_dest_id = l.id
                JOIN
                  product_product pp ON i.product_id = pp.id
              WHERE
                l.usage IN ('internal', 'transit') AND
                state = 'done' AND
                i.company_id = l.company_id
              UNION ALL
              SELECT
                o.id AS id,
                l.id AS location_id,
                pp.default_code,
                product_id,
                o.name,
                CASE
                  WHEN state = 'done' THEN - product_qty
                  ELSE 0
                END AS product_qty,
                o.price_unit,
                o.product_uom AS uom_id,
                date AT TIME ZONE 'UTC-5' AS date,
                o.location_id AS location_org_id,
                o.location_dest_id,
                CASE
                  WHEN o.inventory_id IS NOT NULL THEN 'inventory'
                  WHEN (SELECT sl.usage FROM stock_location sl WHERE sl.id = o.location_dest_id) = 'customer' THEN 'sale'
                  WHEN (SELECT sl.usage FROM stock_location sl WHERE sl.id = o.location_dest_id) = 'supplier' THEN 'purchase'
                  WHEN o.scrapped IS TRUE THEN 'scrap'
                  ELSE 'internal'
                END AS type,
                picking_id,
                l.company_id
              FROM
                stock_location l
                JOIN
                  stock_move o ON o.location_id = l.id
                JOIN
                  product_product pp ON o.product_id = pp.id
              WHERE
                l.usage IN ('internal', 'transit') AND
                state = 'done' AND
                o.company_id = l.company_id)
            """.format(
                self._table
            )
        )
