#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odoo import _, models

PRODUCT_TYPE = {
    "consu": _("Consumable"),
    "service": _("Service"),
    "product": _("Stockable Product"),
}


class StockInventoryRotationReport(models.AbstractModel):
    _name = "report.stock_base_reports.stock_inventory_rotation.xlsx"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, objs):
        warehouse_ids = objs.mapped("warehouse_ids") or objs.warehouse_ids.search([])
        category_ids = objs.mapped("category_ids") or objs.category_ids.search([])
        product_ids = (
            objs.mapped("product_ids").ids
            or self.env["product.product"]
            .search([("categ_id", "in", category_ids.ids)])
            .ids
        )
        header = [
            _("Internal Reference"),
            _("Name"),
            _("Supplier"),
            _("Category"),
            _("Product Type"),
            _("Cost"),
            _("Sales Price"),
            _("Opening Stock"),
            _("Purchase in period"),
            _("Sales in Period"),
            _("Discarded in Period(OUT)"),
            _("Adjusted in Period(IN)"),
            _("Closing Stock"),
            _("Warehouse Transfer(IN)"),
            _("Warehouse Transfer(OUT)"),
            _("Last purchase"),
            _("Last sale"),
        ]
        mr_format = workbook.add_format(
            {"align": "center", "valign": "vcenter", "bold": 1, "font_size": 15}
        )
        header_fromat = workbook.add_format(
            {
                "bold": True,
                "bg_color": "#a7a7a7",
                "border": 1,
                "border_color": "#000000",
            }
        )
        default_format = workbook.add_format({"border": 1, "border_color": "#000000"})
        product_format = workbook.add_format(
            {
                "bg_color": "#9cd9e1",
                "border": 1,
                "border_color": "#000000",
                "num_format": "#,##0.00",
            }
        )
        qty_format = workbook.add_format(
            {
                "bg_color": "#ffa051",
                "num_format": "#,##0.00",
                "border": 1,
                "border_color": "#000000",
            }
        )
        trans_format = workbook.add_format(
            {
                "bg_color": "#f38d37",
                "num_format": "#,##0.00",
                "border": 1,
                "border_color": "#000000",
            }
        )
        alert_format = workbook.add_format(
            {
                "bold": True,
                "bg_color": "#ff5b5b",
                "border": 1,
                "border_color": "#000000",
                "num_format": "#,##0.00",
            }
        )
        pdata_consolidated = {}
        for w in warehouse_ids:
            products = {}
            locations = ",".join(
                map(str, [w.lot_stock_id.id, w.wh_input_stock_loc_id.id])
            )
            for p in product_ids:
                sup_query = """
                SELECT
                  sm.partner_id,
                  sb.date
                FROM stock_base sb
                JOIN stock_move sm ON sb.id = sm.id
                WHERE
                  sb.type = 'purchase'
                  AND sb.location_dest_id IN ({locations})
                  AND sb.product_id = {product}
                  AND sb.date::DATE >= '{dfrom}'
                  AND sb.date::DATE <= '{dto}'
                ORDER BY sb.date DESC
                LIMIT 1
                """.format(
                    locations=locations,
                    product=p,
                    dfrom=objs.from_date,
                    dto=objs.to_date,
                )
                self._cr.execute(sup_query)
                sup_data = self._cr.dictfetchall()
                cus_query = """
                SELECT
                  sb.date
                FROM stock_base sb
                WHERE
                  sb.type = 'sale'
                  AND sb.product_id = {product}
                  AND sb.location_org_id IN ({locations})
                  AND sb.date::DATE >= '{dfrom}'
                  AND sb.date::DATE <= '{dto}'
                ORDER BY sb.date DESC
                LIMIT 1
                """.format(
                    locations=locations,
                    product=p,
                    dfrom=objs.from_date,
                    dto=objs.to_date,
                )
                self._cr.execute(cus_query)
                cus_data = self._cr.dictfetchall()
                ops_query = """
                SELECT
                  SUM(product_qty) AS QTY
                FROM
                  stock_base
                WHERE
                  date::DATE <= '{date}' AND
                  product_id = {product} AND
                  location_id IN ({locations})
                """.format(
                    date=objs.from_date, product=p, locations=locations
                )
                self._cr.execute(ops_query)
                ops_data = self._cr.dictfetchall()
                cls_query = """
                SELECT
                  SUM(product_qty) AS QTY
                FROM
                  stock_base
                WHERE
                  date::DATE <= '{date}' AND
                  product_id = {product} AND
                  location_id IN ({locations})
                """.format(
                    date=objs.to_date, product=p, locations=locations
                )
                self._cr.execute(cls_query)
                cls_data = self._cr.dictfetchall()
                trasnfer_in_query = """
                SELECT
                  SUM(ABS(product_qty)) AS QTY
                FROM
                  stock_base
                WHERE
                  date::DATE >= '{dfrom}' AND
                  date::DATE <= '{dto}' AND
                  product_id = {product} AND
                  type = 'internal' AND
                  location_dest_id IN ({locations})
                """.format(
                    locations=locations,
                    product=p,
                    dfrom=objs.from_date,
                    dto=objs.to_date,
                )
                self._cr.execute(trasnfer_in_query)
                trasnfer_in_data = self._cr.dictfetchall()
                trasnfer_out_query = """
                SELECT
                  SUM(ABS(product_qty)) AS QTY
                FROM
                  stock_base
                WHERE
                  date::DATE >= '{dfrom}' AND
                  date::DATE <= '{dto}' AND
                  product_id = {product} AND
                  type = 'internal' AND
                  location_org_id IN ({locations})
                """.format(
                    locations=locations,
                    product=p,
                    dfrom=objs.from_date,
                    dto=objs.to_date,
                )
                self._cr.execute(trasnfer_out_query)
                trasnfer_out_data = self._cr.dictfetchall()
                products[p] = {
                    "partner_id": sup_data[0].get("partner_id", False)
                    if sup_data
                    else False,
                    "last_purchase": sup_data[0].get("date", False)
                    if sup_data
                    else False,
                    "last_sale": cus_data[0].get("date", False) if cus_data else False,
                    "ops_qty": ops_data[0].get("qty", False) if ops_data else 0,
                    "cls_qty": cls_data[0].get("qty", False) if cls_data else 0,
                    "trasnfer_in_qty": trasnfer_in_data[0].get("qty", False)
                    if trasnfer_in_data
                    else 0,
                    "transfer_out_qty": trasnfer_out_data[0].get("qty", False)
                    if trasnfer_out_data
                    else 0,
                    "sale": 0,
                    "purchase": 0,
                    "scrap": 0,
                    "inventory": 0,
                    "internal": 0,
                }
            query = """
            SELECT
              product_id,
              type,
              product_qty
            FROM
              stock_base
            WHERE
              location_id IN ({locations}) AND
              product_id IN ({products}) AND
              date >= '{dfrom}' AND
              date <= '{dto}'
            ORDER BY product_id
            """.format(
                locations=locations,
                products=",".join(map(str, product_ids)),
                dfrom=objs.from_date,
                dto=objs.to_date,
            )
            self._cr.execute(query)
            pdata = self._cr.dictfetchall()
            if pdata:
                sheet = workbook.add_worksheet(w.name)
                for pd in pdata:
                    products[pd.get("product_id", False)][pd.get("type", False)] += abs(
                        pd.get("product_qty", False)
                    )
                mr_range = "A1:Q1"
                sheet.merge_range(
                    mr_range,
                    _(
                        "Stock Rotation {} from {} to {}".format(
                            w.name, objs.from_date, objs.to_date
                        )
                    ),
                    mr_format,
                )
                sheet.write_row(1, 0, header, header_fromat)
                sheet.autofilter("A2:Q2")
                sheet.fit_to_pages(1, 0)
                sheet.freeze_panes(2, 0)
                i = 2
                for p, v in products.items():
                    if not (
                        v.get("ops_qty")
                        or v.get("sale")
                        or v.get("purchase")
                        or v.get("scrap")
                        or v.get("inventory")
                        or v.get("cls_qty")
                        or v.get("transfer_in_qty")
                        or v.get("transfer_out_qty")
                    ):
                        pass

                    product = self.env["product.product"].browse(p)
                    product = product.with_context(warehouse=w.id, to_date=objs.to_date)
                    partner = self.env["res.partner"].browse(v.get("partner_id"))
                    sheet.write(i, 0, product.default_code, default_format)
                    sheet.write(i, 1, product.name, default_format)
                    sheet.write(i, 2, partner.name if partner else "", product_format)
                    sheet.write(i, 3, product.categ_id.name, product_format)
                    sheet.write(i, 4, PRODUCT_TYPE[product.type], product_format),
                    sheet.write(i, 5, product.standard_price, product_format)
                    sheet.write(i, 6, product.lst_price, product_format)
                    sheet.write(i, 7, v.get("ops_qty") or 0, qty_format)
                    sheet.write(i, 8, v.get("purchase"), qty_format)
                    sheet.write(i, 9, v.get("sale"), qty_format)
                    sheet.write(i, 10, v.get("scrap"), qty_format)
                    sheet.write(i, 11, v.get("inventory"), qty_format)
                    sheet.write(i, 12, v.get("cls_qty") or 0, qty_format)
                    sheet.write(i, 13, v.get("transfer_in_qty") or 0, trans_format)
                    sheet.write(i, 14, v.get("transfer_out_qty") or 0, trans_format)
                    sheet.write(i, 15, v.get("last_purchase") or "", default_format)
                    sheet.write(i, 16, v.get("last_sale") or "", default_format)
                    if objs.consolidated:
                        if not pdata_consolidated.get(p, False):
                            pdata_consolidated.update(
                                {
                                    p: {
                                        "code": product.default_code,
                                        "name": product.name,
                                        "partner": "",
                                        "categ": product.categ_id.name,
                                        "type": PRODUCT_TYPE[product.type],
                                        "cost": product.standard_price,
                                        "price": product.lst_price,
                                        "ops_qty": 0,
                                        "sale": 0,
                                        "purchase": 0,
                                        "scrap": 0,
                                        "inventory": 0,
                                        "cls_qty": 0,
                                        "in_qty": 0,
                                        "out_qty": 0,
                                        "last_purchase": [],
                                        "last_sale": [],
                                    }
                                }
                            )
                        pdata_consolidated[p]["ops_qty"] += v.get("ops_qty") or 0
                        pdata_consolidated[p]["sale"] += v.get("sale") or 0
                        pdata_consolidated[p]["purchase"] += v.get("purchase") or 0
                        pdata_consolidated[p]["scrap"] += v.get("scrap") or 0
                        pdata_consolidated[p]["inventory"] += v.get("inventory") or 0
                        pdata_consolidated[p]["cls_qty"] += v.get("cls_qty") or 0
                        pdata_consolidated[p]["in_qty"] += v.get("transfer_in_qty") or 0
                        pdata_consolidated[p]["out_qty"] += (
                            v.get("transfer_out_qty") or 0
                        )
                        pdata_consolidated[p]["last_purchase"] += [
                            v.get("last_purchase") or ""
                        ]
                        pdata_consolidated[p]["last_sale"] += [v.get("last_sale") or ""]
                    i += 1
                sheet.conditional_format(
                    "A3:Q{}".format(i),
                    {
                        "type": "cell",
                        "criteria": "<",
                        "value": 0,
                        "format": alert_format,
                    },
                )
        if objs.consolidated and pdata_consolidated:
            sheet = workbook.add_worksheet("Consolidated")
            mr_range = "A1:Q1"
            sheet.merge_range(
                mr_range,
                _("Stock Rotation from {} to {}".format(objs.from_date, objs.to_date)),
                mr_format,
            )
            sheet.write_row(1, 0, header, header_fromat)
            sheet.autofilter("A2:Q2")
            i = 2
            for p, v in pdata_consolidated.items():
                sheet.write(i, 0, v.get("code"), default_format)
                sheet.write(i, 1, v.get("name"), default_format)
                sheet.write(i, 2, v.get("partner"), product_format)
                sheet.write(i, 3, v.get("categ"), product_format)
                sheet.write(i, 4, v.get("type"), product_format),
                sheet.write(i, 5, v.get("cost"), product_format)
                sheet.write(i, 6, v.get("price"), product_format)
                sheet.write(i, 7, v.get("ops_qty") or 0, qty_format)
                sheet.write(i, 8, v.get("purchase"), qty_format)
                sheet.write(i, 9, v.get("sale"), qty_format)
                sheet.write(i, 10, v.get("scrap"), qty_format)
                sheet.write(i, 11, v.get("inventory"), qty_format)
                sheet.write(i, 12, v.get("cls_qty") or 0, qty_format)
                sheet.write(i, 13, v.get("in_qty") or 0, trans_format)
                sheet.write(i, 14, v.get("out_qty") or 0, trans_format)
                sheet.write(i, 15, max(v.get("last_purchase")) or "", default_format)
                sheet.write(i, 16, max(v.get("last_sale")) or "", default_format)
                i += 1
            sheet.conditional_format(
                "A3:Q{}".format(i),
                {"type": "cell", "criteria": "<", "value": 0, "format": alert_format},
            )
