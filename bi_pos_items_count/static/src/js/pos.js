// bi_pos_items_count js
//console.log("custom callleddddddddddddddddddddd")
odoo.define('bi_pos_items_count.pos', function(require) {
    "use strict";

    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var gui = require('point_of_sale.gui');
    var popups = require('point_of_sale.popups');
    var QWeb = core.qweb;

    var _t = core._t;



    // exports.OrderWidget = Backbone.Model.extend ...
    var OrderWidgetExtended = screens.OrderWidget.include({

		update_summary: function(){
		    var order = this.pos.get_order();
		    if (!order.get_orderlines().length) {
		        return;
		    }

		    var total     = order ? order.get_total_with_tax() : 0;
		    var taxes     = order ? total - order.get_total_without_tax() : 0;
		    var total_items    = order ? order.get_total_items() : 0;

		    this.el.querySelector('.summary .total > .value').textContent = this.format_currency(total);
		    this.el.querySelector('.summary .total .subentry .value').textContent = this.format_currency(taxes);
		    this.el.querySelector('.items .value').textContent = total_items;

		},
    });
    


   // exports.Orderline = Backbone.Model.extend ...
   var OrderSuper = models.Order;
    models.Order = models.Order.extend({

	    get_total_items: function() {
           var utils = require('web.utils');
           var round_pr = utils.round_precision;
            
             return round_pr(this.orderlines.reduce((function(sum, orderLine) {
            return sum + orderLine.quantity;

        }), 0), this.pos.currency.rounding);
    sum
        },
    
    });
    
    


});
