# -*- coding: utf-8 -*-
import base64
import datetime
import logging
import pdb
from datetime import datetime, timedelta
from io import BytesIO
from itertools import chain

from dateutil import parser
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

try:
    import xlwt
    from xlwt import Borders
except ImportError:
    xlwt = None


class ExportStockInfoReport(models.TransientModel):

    _name = "export.stockinfo.report.ept"

    datas = fields.Binary("File")

    is_active_product = fields.Boolean(string="Active Products Only?")
    is_display_red = fields.Boolean(
        string="Display Red Text for Negative Quantity ?", default=True
    )

    report_wise = fields.Selection(
        [("Warehouse", "Warehouse"), ("Location", "Location")],
        string="Generate Report Based on",
        default="Warehouse",
    )

    to_date = fields.Datetime(string="To Date")

    supplier_ids = fields.Many2many(
        "res.partner",
        "supplier_wizard_ids",
        "wizard_id",
        "supplier_id",
        string="Supplier",
        domain="[('supplier','=',True)]",
    )
    category_ids = fields.Many2many(
        "product.category",
        "product_category_wizard_res",
        "wizard_id",
        "categ_id",
        string="Category",
    )
    warehouse_ids = fields.Many2many(
        "stock.warehouse",
        "stock_warehouse_wizard_res",
        "wizard_id",
        "warehouse_id",
        string="Warehouse",
    )
    location_ids = fields.Many2many(
        "stock.location",
        "stock_location_wizard_rel",
        "wizard_id",
        "location_id",
        string="Locations",
    )

    @api.multi
    def print_stock_info_report_xls(self):
        product_obj = self.env["product.product"]
        active_id = self.ids[0]
        to_date = self.to_date

        today = datetime.now().strftime("%Y-%m-%d")
        f_name = "Product Stock Info " + " " + today
        logging.info("Init export")
        if not self.report_wise:
            raise UserError(_("Please select the report Genration Based On"))

        if not (self.warehouse_ids or self.location_ids):
            raise UserError(_("Please select the %s" % (self.report_wise)))

        domain = [("type", "!=", "service")]
        if self.supplier_ids:
            supplier_ids = [x.id for x in self.supplier_ids]
            domain.append(("seller_ids.name", "in", supplier_ids))
        if self.category_ids:
            category_ids = [x.id for x in self.category_ids]
            domain.append(("categ_id", "child_of", category_ids))
        if self.is_active_product:
            all_product_ids = product_obj.search(domain)
        else:
            domain.extend(["|", ("active", "=", True), ("active", "=", False)])
            all_product_ids = product_obj.search(domain)
        warehouse_or_location = False
        if self.report_wise == "Warehouse":
            warehouse_or_location = self.warehouse_ids.ids
        else:
            warehouse_or_location = self.location_ids.ids
        logging.info("get products")
        self.generate_export_stockinfo_report(
            today, to_date, all_product_ids, warehouse_or_location
        )
        if self.datas:
            return {
                "type": "ir.actions.act_url",
                "url": "web/content/?model=export.stockinfo.report.ept&download=true&field=datas&id=%s&filename=%s.xls"
                % (active_id, f_name),
                "target": "self",
            }

    @api.multi
    def generate_export_stockinfo_report(
        self, today, to_date, all_product_ids, warehouse_or_location
    ):
        warehouse_obj = self.env["stock.warehouse"]
        location_obj = self.env["stock.location"]
        location_lst = []
        warehouse_ids = False
        if self.report_wise == "Warehouse":
            warehouse_ids = warehouse_obj.search([("id", "in", warehouse_or_location)])
        else:
            if not warehouse_ids:
                sql_stock = "SELECT id FROM stock_location WHERE id in {}".format(
                    "(" + str(warehouse_or_location or [0]).strip("[]") + ")"
                )
                self.env.cr.execute(sql_stock)
                location_ids = self.env.cr.fetchall()
                if location_ids:
                    for location in location_ids:
                        child_list = self.get_child_locations(location[0])
                        location_lst.append(child_list)
                    locations = location_obj.browse(
                        list(set(list(chain(*location_lst))))
                    )
                else:
                    return True

        workbook, header_bold, body_style, style, header_title, ware_or_loc_header_style, red_font_style, cost_cell_style, worksheet_available_virtual_style, blank_cell_style, worksheet_incoming_outgoing_net_style, worksheet_totalsoldqty_totalpurchasedqty_style, worksheet_valuation_style = (
            self.create_sheet()
        )

        workbook, new_workbook, row_data = self.add_headings(
            warehouse_ids or locations,
            today,
            to_date,
            workbook,
            header_bold,
            header_title,
            ware_or_loc_header_style,
            blank_cell_style,
        )

        single_data_dict = self.prepare_data(
            today, all_product_ids, warehouse_or_location
        )
        self.print_ware_or_loc_data(
            single_data_dict,
            all_product_ids,
            new_workbook,
            row_data,
            red_font_style,
            cost_cell_style,
            worksheet_available_virtual_style,
            blank_cell_style,
            worksheet_incoming_outgoing_net_style,
            worksheet_totalsoldqty_totalpurchasedqty_style,
            worksheet_valuation_style,
        )

        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        sale_file = base64.encodebytes(fp.read())
        fp.close()
        self.write({"datas": sale_file})

        return True

    @api.multi
    def create_sheet(self):
        workbook = xlwt.Workbook()

        borders = Borders()
        header_border = Borders()
        header_title_border = Borders()
        ware_or_loc_border = Borders()
        header_border.left, header_border.right, header_border.top, header_border.bottom = (
            Borders.THIN,
            Borders.THIN,
            Borders.THIN,
            Borders.THICK,
        )
        header_title_border.left, header_title_border.right, header_title_border.top, header_title_border.bottom = (
            Borders.THIN,
            Borders.THIN,
            Borders.THIN,
            Borders.THICK,
        )
        ware_or_loc_border.left, ware_or_loc_border.right, ware_or_loc_border.top, ware_or_loc_border.bottom = (
            Borders.THIN,
            Borders.THIN,
            Borders.THIN,
            Borders.THICK,
        )
        borders.left, borders.right, borders.top, borders.bottom = (
            Borders.THIN,
            Borders.THIN,
            Borders.THIN,
            Borders.THIN,
        )
        header_bold = xlwt.easyxf(
            "font: bold on, height 250; pattern: pattern solid, fore_colour gray25;alignment: horizontal center ,vertical center"
        )
        header_bold.borders = header_border
        body_style = xlwt.easyxf("font: height 200; alignment: horizontal center")
        style = xlwt.easyxf(
            "font: height 210, bold True; alignment: horizontal center,vertical center;borders: top medium,right medium,bottom medium,left medium"
        )
        body_style.borders = borders

        header_title = xlwt.easyxf(
            "font: bold on, height 315; pattern: pattern solid, fore_colour gray25;alignment: horizontal center ,vertical center"
        )
        header_title.borders = header_title_border

        ware_or_loc_header_style = xlwt.easyxf(
            "font: bold on, height 315; pattern: pattern solid, fore_colour gray25;alignment: horizontal center ,vertical center"
        )
        ware_or_loc_header_style.borders = ware_or_loc_border

        red_font_style = xlwt.easyxf(
            "font: bold on; pattern: pattern solid, fore_colour red;"
        )

        xlwt.add_palette_colour("custom_indigo", 0x31)
        workbook.set_colour_RGB(0x31, 209, 196, 233)
        cost_cell_style = xlwt.easyxf(
            "font: height 200,bold on, name Arial; align: horiz right, vert center;  pattern: pattern solid, fore_colour custom_indigo;  borders: top thin,right thin,bottom thin,left thin"
        )
        cost_cell_style.string_num_format = "0.00"

        xlwt.add_palette_colour("light_blue_21", 0x25)
        workbook.set_colour_RGB(0x25, 179, 255, 240)
        worksheet_available_virtual_style = xlwt.easyxf(
            "font: height 200,bold on, name Arial; align: horiz right, vert center;  pattern: pattern solid, fore_colour light_blue_21;  borders: top thin,right thin,bottom thin,left thin"
        )
        worksheet_available_virtual_style.string_num_format = "0.00"

        xlwt.add_palette_colour("custom_yellow", 0x21)
        workbook.set_colour_RGB(0x21, 255, 255, 179)
        blank_cell_style = xlwt.easyxf(
            "font: height 200,bold on, name Arial; align: horiz right, vert center;  pattern: pattern solid, fore_colour custom_yellow;  borders: top thin,right thin,bottom thin,left thin"
        )

        xlwt.add_palette_colour("custom_pink", 0x23)
        workbook.set_colour_RGB(0x23, 255, 204, 204)
        worksheet_incoming_outgoing_net_style = xlwt.easyxf(
            "font: height 200,bold on, name Arial; align: horiz right, vert center;  pattern: pattern solid, fore_colour custom_pink;  borders: top thin,right thin,bottom thin,left thin"
        )
        worksheet_incoming_outgoing_net_style.string_num_format = "0.00"

        xlwt.add_palette_colour("custom_green", 0x24)
        workbook.set_colour_RGB(0x24, 204, 255, 204)
        worksheet_totalsoldqty_totalpurchasedqty_style = xlwt.easyxf(
            "font: height 200,bold on, name Arial; align: horiz right, vert center;  pattern: pattern solid, fore_colour custom_green;  borders: top thin,right thin,bottom thin,left thin"
        )
        worksheet_totalsoldqty_totalpurchasedqty_style.string_num_format = "0.00"

        xlwt.add_palette_colour("custom_orange", 0x22)
        workbook.set_colour_RGB(0x22, 255, 204, 153)
        worksheet_valuation_style = xlwt.easyxf(
            "font: height 200,bold on, name Arial; align: horiz right, vert center;  pattern: pattern solid, fore_colour custom_orange;  borders: top thin,right thin,bottom thin,left thin"
        )
        worksheet_valuation_style.string_num_format = "0.00"

        return (
            workbook,
            header_bold,
            body_style,
            style,
            header_title,
            ware_or_loc_header_style,
            red_font_style,
            cost_cell_style,
            worksheet_available_virtual_style,
            blank_cell_style,
            worksheet_incoming_outgoing_net_style,
            worksheet_totalsoldqty_totalpurchasedqty_style,
            worksheet_valuation_style,
        )

    @api.multi
    def add_headings(
        self,
        locations_or_warehouses,
        today,
        to_date,
        workbook,
        header_bold,
        header_title,
        ware_or_loc_header_style,
        blank_cell_style,
    ):
        row_data = {}

        new_workbook = workbook.add_sheet(_("Product Stock"), cell_overwrite_ok=True)

        if to_date:
            string_reportdate = _("Report Date : " + to_date)
        else:
            string_reportdate = _("Report Date : " + today)

        new_workbook.write_merge(2, 2, 0, 2, string_reportdate, header_bold)
        new_workbook.write_merge(3, 3, 0, 5, _("Product Information"), header_bold)

        if self.report_wise == "Warehouse":
            string_warehouse_or_locations = _("Warehouse(s)")
        else:
            string_warehouse_or_locations = _("Location(s)")

        new_workbook.row(2).height = 375
        new_workbook.row(3).height = 400
        new_workbook.row(4).height = 400

        new_workbook.col(1).width = 6000
        new_workbook.col(2).width = 4000
        new_workbook.col(3).width = 8000
        new_workbook.col(4).width = 5500
        new_workbook.col(5).width = 3500

        # First Warehouse Column
        new_workbook.col(6).width = 4000
        new_workbook.col(7).width = 4000
        new_workbook.col(8).width = 1000
        new_workbook.col(9).width = 4000
        new_workbook.col(10).width = 4000
        new_workbook.col(11).width = 5500
        new_workbook.col(12).width = 4200
        new_workbook.col(13).width = 2800
        new_workbook.col(14).width = 1800
        new_workbook.col(15).width = 4200
        new_workbook.col(16).width = 1000

        # Second Warehouse Column
        new_workbook.col(18).width = 4000
        new_workbook.col(19).width = 4200
        new_workbook.col(20).width = 1000
        new_workbook.col(21).width = 4000
        new_workbook.col(22).width = 4000
        new_workbook.col(23).width = 5500
        new_workbook.col(24).width = 4200
        new_workbook.col(25).width = 2800
        new_workbook.col(26).width = 1800
        new_workbook.col(27).width = 4200
        new_workbook.col(28).width = 1000

        # Third Warehouse Column
        new_workbook.col(30).width = 4000
        new_workbook.col(31).width = 4200
        new_workbook.col(32).width = 1000
        new_workbook.col(33).width = 4000
        new_workbook.col(34).width = 4000
        new_workbook.col(35).width = 5500
        new_workbook.col(36).width = 4200
        new_workbook.col(37).width = 1800
        new_workbook.col(38).width = 5800
        new_workbook.col(39).width = 4200
        new_workbook.col(40).width = 1000

        # Fourth Warehouse Column
        new_workbook.col(42).width = 4000
        new_workbook.col(43).width = 4200
        new_workbook.col(44).width = 1000
        new_workbook.col(45).width = 4000
        new_workbook.col(46).width = 4000
        new_workbook.col(47).width = 5500
        new_workbook.col(48).width = 4200
        new_workbook.col(49).width = 1800
        new_workbook.col(50).width = 5800
        new_workbook.col(51).width = 4200
        new_workbook.col(52).width = 1000

        # Five Warehouse Column
        new_workbook.col(54).width = 4000
        new_workbook.col(55).width = 4200
        new_workbook.col(56).width = 1000
        new_workbook.col(57).width = 4000
        new_workbook.col(58).width = 4000
        new_workbook.col(59).width = 5500
        new_workbook.col(60).width = 4200
        new_workbook.col(61).width = 1800
        new_workbook.col(62).width = 5800
        new_workbook.col(63).width = 4200
        new_workbook.col(64).width = 1000

        new_workbook.write(4, 0, _("State"), header_bold)
        new_workbook.write(4, 1, _("Supplier"), header_bold)
        new_workbook.write(4, 2, _("SKU"), header_bold)
        new_workbook.write(4, 3, _("Barcode"), header_bold)
        new_workbook.write(4, 4, _("Name"), header_bold)
        new_workbook.write(4, 5, _("Category"), header_bold)
        new_workbook.write(4, 6, _("Cost"), header_bold)

        col2 = 4
        if len(locations_or_warehouses) == 1:
            col2 = 16
        else:
            for warehouse_or_location in locations_or_warehouses:
                col2 += 12
        new_workbook.write_merge(
            2, 2, 7, col2, string_warehouse_or_locations, ware_or_loc_header_style
        )

        row = 4
        col = 7
        header_warehouse_row = 3
        header_warehouse_column = 7
        for warehouse_or_location in locations_or_warehouses:
            new_workbook.write_merge(
                header_warehouse_row,
                header_warehouse_row,
                header_warehouse_column,
                header_warehouse_column + 10,
                warehouse_or_location.name,
                header_title,
            )
            new_workbook.write(row, col, _("Available Qty"), header_bold)
            new_workbook.write(row, col + 1, None, blank_cell_style)

            new_workbook.write(row, col + 2, _("Incoming Qty"), header_bold)
            new_workbook.write(row, col + 3, _("Outgoing Qty"), header_bold)
            new_workbook.write(row, col + 4, _("Net On Hand"), header_bold)
            new_workbook.write(row, col + 5, _("Forecasted Stock"), header_bold)

            new_workbook.write(row, col + 6, None, blank_cell_style)

            new_workbook.write(row, col + 7, _("Total Sold Qty"), header_bold)
            new_workbook.write(row, col + 8, _("Total Purchased Qty",) header_bold)

            new_workbook.write(row, col + 9, None, blank_cell_style)

            new_workbook.write(row, col + 10, _("Valuation"), header_bold)
            col += 12
            header_warehouse_column += 12

        new_workbook.set_panes_frozen(True)
        new_workbook.set_horz_split_pos(5)
        row_data.update({new_workbook: 5})

        return workbook, new_workbook, row_data

    @api.multi
    def prepare_data(self, today, all_product_ids, warehouse_or_location):
        single_data_dict = {}
        if self.report_wise == "Warehouse":
            sql_stock = "SELECT id, view_location_id FROM stock_warehouse WHERE id in {}".format(
                "(" + str(warehouse_or_location or [0]).strip("[]") + ")"
            )
            self.env.cr.execute(sql_stock)
            warehouse_ids = self.env.cr.fetchall()
            for warehouse in warehouse_ids:
                child_locations_list = self.get_child_locations(warehouse[1])
                stock_data = self.get_data_ware_or_loc(
                    child_locations_list, all_product_ids
                )
                single_data_dict.update({warehouse[0]: stock_data})
        else:
            sql = "SELECT id FROM stock_location WHERE id in {}".format(
                "(" + str(warehouse_or_location or [0]).strip("[]") + ")"
            )
            self.env.cr.execute(sql)
            locations_ids = self.env.cr.fetchall()
            for location in locations_ids:
                stock_data = self.get_data_ware_or_loc(location[0], all_product_ids)
                single_data_dict.update({location[0]: stock_data})
        return single_data_dict

    @api.model
    def get_data_ware_or_loc(self, child_locations_list, all_product_ids):
        sql_stock = "SELECT id FROM stock_location WHERE usage = '{}'".format(
            "customer"
        )
        self.env.cr.execute(sql_stock)
        customer_location_ids = self.env.cr.fetchall()
        sql = "SELECT id FROM stock_location WHERE usage = '{}'".format("supplier")
        self.env.cr.execute(sql)
        supplier_location_ids = self.env.cr.fetchall()
        customer_location = [supplier[0] for supplier in customer_location_ids]
        customer_location_ids = "(" + str(customer_location or [0]).strip("[]") + ")"
        supplier_location = [supplier[0] for supplier in supplier_location_ids]
        supplier_location_ids = "(" + str(supplier_location or [0]).strip("[]") + ")"

        if type(child_locations_list) == type(1):
            location_ids = [child_locations_list]
        elif type(child_locations_list) == type([]):
            location_ids = child_locations_list
        else:
            raise Warning(
                "Please give correct location value. It must be list of location ids or integer."
            )
        date_filter = ""
        if self.to_date:
            date_filter = date_filter + "and date::date <=" + "'" + self.to_date + "'"

        if not all_product_ids:
            return []
        product_ids = "(" + str(all_product_ids.ids).strip("[]") + ")"
        location_ids = "(" + str(location_ids or [0]).strip("[]") + ")"
        qry = """
select product,
COALESCE(sum(report.qty_available),0) as qty_available,
COALESCE(sum(report.valuation),0) as valuation,
COALESCE(sum(report.qty_available),0)+COALESCE(sum(report.incoming),0)-COALESCE(sum(report.outgoing),0) as virtual_available,
sum(incoming) as incoming_qty,
sum(outgoing) as outgoing_qty,
sum(sold) as sold,
sum(purchased) as purchased  from
(
select product,sum(qty) as qty_available ,sum(valuation) as valuation,0 as incoming, 0 as outgoing,0 as sold, 0 as purchased from
    (select mv.product_id as product, mv.product_qty as qty ,(mv.price_unit * mv.product_uom_qty ) as valuation from stock_move as mv
    where product_id in %s and location_dest_id in %s and state ='done' %s

    union all

    select mv.product_id as product, -mv.product_qty as qty ,(mv.price_unit * mv.product_uom_qty ) as valuation from stock_move as mv
    where product_id in %s and location_id in %s and state ='done' %s

    ) as product_stock_available group by product

union all
Select prod as product,0 as qty_available,0 as valuation, sum(stock_in_out_data.in) as incoming, sum(stock_in_out_data.out) as outgoing,0 as sold, 0 as purchased from
                (
                Select product_id as prod, sum(product_qty) as in, 0 as out from stock_move
                    where
                    product_id in %s
                    and location_id not in %s and location_dest_id in %s
                    and state in ('confirmed', 'waiting', 'assigned') %s
                    group by product_id
                UNION
                Select product_id as prod, 0 as in, sum(product_qty) as out from stock_move
                    where
                    product_id in %s
                    and location_id in %s and location_dest_id not in %s
                    and state in ('confirmed', 'waiting', 'assigned') %s
                    group by product_id
                ) as stock_in_out_data
                group by prod
union all
select stock_data.prod as product,0 as qty_available,0 as valuation,0 as incoming,0 as outgoing, sum(stock_data.sold) as sold, sum(stock_data.purchased) as purchased
        from (
                Select product_id as prod, sum(product_qty) as sold, 0 as purchased from stock_move
                    where
                    product_id in %s
                    and location_id in %s and location_dest_id in %s
                    and state='done' %s
                    group by product_id
                UNION
                Select product_id as prod, 0 as sold, sum(product_qty) as purchased from stock_move
                    where
                    product_id in %s
                    and location_id in %s and location_dest_id in %s
                    and state='done' %s
                    group by product_id
                ) as stock_data group by prod
               ) report
JOIN product_product P on (P.id = report.product)
group by product order by product
        """ % (
            product_ids,
            location_ids,
            date_filter,
            product_ids,
            location_ids,
            date_filter,
            product_ids,
            location_ids,
            location_ids,
            date_filter,
            product_ids,
            location_ids,
            location_ids,
            date_filter,
            product_ids,
            location_ids,
            customer_location_ids,
            date_filter,
            product_ids,
            supplier_location_ids,
            location_ids,
            date_filter,
        )
        self._cr.execute(qry)
        execute_qry = self._cr.dictfetchall()
        stock_product = dict(map(lambda x: (x.get("product"), x), execute_qry))
        return stock_product

    @api.multi
    def get_child_locations(self, location):
        child_list = []
        child_list.append(location)
        # # finding all child of given location
        sql = "SELECT id FROM stock_location WHERE usage = '{}' and location_id = '{}'".format(
            "internal", location
        )
        self.env.cr.execute(sql)
        child_locations_obj = self.env.cr.fetchall()

        if child_locations_obj:
            for child_location in child_locations_obj:
                # child_list.append(child_location.id)
                child_list.append(child_location[0])
                children_loc = self.get_child_locations(child_location[0])
                for child in children_loc:
                    child_list.append(child)
        return child_list

    @api.multi
    def print_ware_or_loc_data(
        self,
        single_data_dict,
        all_product_ids,
        new_workbook,
        row_data,
        red_font_style,
        cost_cell_style,
        worksheet_available_virtual_style,
        blank_cell_style,
        worksheet_incoming_outgoing_net_style,
        worksheet_totalsoldqty_totalpurchasedqty_style,
        worksheet_valuation_style,
    ):

        column = 0
        row = 5
        for product in all_product_ids:
            status = "Active" if product.active else "Inactive"
            supplier_name = product.seller_ids and product.seller_ids[0].name.name or ""
            name = product.name or ""
            category = product.categ_id and product.categ_id.name or ""

            new_workbook.write(row, column, status)
            new_workbook.write(row, column + 1, supplier_name)
            new_workbook.write(row, column + 2, product.default_code or "")
            new_workbook.write(row, column + 3, product.barcode or "")
            new_workbook.write(row, column + 4, name)
            new_workbook.write(row, column + 5, category)
            new_workbook.write(row, column + 6, product.standard_price, cost_cell_style)

            new_column = 7
            for single_data in single_data_dict:

                qty_available = (
                    single_data_dict[single_data]
                    .get(product.id, {})
                    .get("qty_available", 0)
                )
                virtual_available = (
                    single_data_dict[single_data]
                    .get(product.id, {})
                    .get("virtual_available", 0)
                )
                incoming_qty = (
                    single_data_dict[single_data]
                    .get(product.id, {})
                    .get("incoming_qty", 0)
                )
                outgoing_qty = (
                    single_data_dict[single_data]
                    .get(product.id, {})
                    .get("outgoing_qty", 0)
                )
                sold_qty = (
                    single_data_dict[single_data].get(product.id, {}).get("sold", 0)
                )
                purchased_qty = (
                    single_data_dict[single_data]
                    .get(product.id, {})
                    .get("purchased", 0)
                )
                valuation = (
                    single_data_dict[single_data]
                    .get(product.id, {})
                    .get("valuation", 0)
                )

                if product.cost_method != "real":
                    valuation = qty_available * product.standard_price
                net_on_hand = qty_available - outgoing_qty

                if qty_available < 0 and self.is_display_red:
                    new_workbook.write(row, new_column, qty_available, red_font_style)
                else:
                    new_workbook.write(
                        row,
                        new_column,
                        qty_available,
                        worksheet_available_virtual_style,
                    )

                new_workbook.write(row, new_column + 1, None, blank_cell_style)

                if incoming_qty < 0 and self.is_display_red:
                    new_workbook.write(
                        row, new_column + 2, incoming_qty, red_font_style
                    )
                else:
                    new_workbook.write(
                        row,
                        new_column + 2,
                        incoming_qty,
                        worksheet_incoming_outgoing_net_style,
                    )
                if outgoing_qty < 0 and self.is_display_red:
                    new_workbook.write(
                        row, new_column + 3, outgoing_qty, red_font_style
                    )
                else:
                    new_workbook.write(
                        row,
                        new_column + 3,
                        outgoing_qty,
                        worksheet_incoming_outgoing_net_style,
                    )
                if net_on_hand < 0 and self.is_display_red:
                    new_workbook.write(row, new_column + 4, net_on_hand, red_font_style)
                else:
                    new_workbook.write(
                        row,
                        new_column + 4,
                        net_on_hand,
                        worksheet_incoming_outgoing_net_style,
                    )

                if virtual_available < 0 and self.is_display_red:
                    new_workbook.write(
                        row, new_column + 5, virtual_available, red_font_style
                    )
                else:
                    new_workbook.write(
                        row,
                        new_column + 5,
                        virtual_available,
                        worksheet_available_virtual_style,
                    )

                new_workbook.write(row, new_column + 6, None, blank_cell_style)

                new_workbook.write(
                    row,
                    new_column + 7,
                    sold_qty,
                    worksheet_totalsoldqty_totalpurchasedqty_style,
                )
                new_workbook.write(
                    row,
                    new_column + 8,
                    purchased_qty,
                    worksheet_totalsoldqty_totalpurchasedqty_style,
                )

                new_workbook.write(row, new_column + 9, None, blank_cell_style)

                if valuation < 0 and self.is_display_red:
                    new_workbook.write(row, new_column + 10, valuation, red_font_style)
                else:
                    new_workbook.write(
                        row, new_column + 10, valuation, worksheet_valuation_style
                    )
                new_column += 12
            row += 1
            column = 0
        return True

    @api.model
    def auto_generator_export_stockinfo_report(self):
        today = datetime.now().strftime("%Y-%m-%d")
        f_name = "Product Stock Info" + " " + today + ".xls"
        product_stockinfo_id = self.create({})
        product_obj = self.env["product.product"]
        warehouse_obj = self.env["stock.warehouse"]
        product_ids = product_obj.search([("type", "!=", "service")])
        warehouse_id = warehouse_obj.search([])
        warehouse_ids = warehouse_id.ids
        product_stockinfo_id.generate_export_stockinfo_report(
            today, today, product_ids, warehouse_ids
        )
        vals = {
            "name": "Product Stock Info.xls",
            "datas": product_stockinfo_id.datas,
            "datas_fname": f_name,
            "type": "binary",
            "res_model": "export.stockinfo.report.ept",
        }

        attachment_id = self.env["ir.attachment"].create(vals)
        mail_template_view = self.env.ref(
            "ec_11_export_stock.mail_template_export_stockinfo_report_ept"
        )
        msg_ids = mail_template_view.send_mail(product_stockinfo_id.id)
        mail_brow_obj = self.env["mail.mail"].browse(msg_ids)
        mail_brow_obj.write({"attachment_ids": [(6, 0, [attachment_id.id])]})
        mail_brow_obj.send()

    @api.multi
    def print_stock_info_report_pdf(self):
        return self.env.ref(
            "ec_11_export_stock.export_stockinfo_reprot_pdf_action"
        ).report_action(self)
