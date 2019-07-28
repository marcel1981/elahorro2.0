odoo.define('ec_pos_ajust.promotion', function (require) {
"use strict";

    var screens = require('point_of_sale.screens');
	var models = require('point_of_sale.models');
    var pos_promotion = models.PosModel.prototype.models.filter(x => x.model =='pos.promotion')[0];
    var core = require('web.core');
    var utils = require('web.utils');
    var round_pr = utils.round_precision;
    var _t = core._t;
    var gui = require('point_of_sale.gui');
    var qweb = core.qweb;

    pos_promotion.domain = function(self){
        var current_date = moment(new Date()).locale('en').format("YYYY-MM-DD");
        return [
            ['from_date','<=',current_date],
            ['to_date','>=',current_date],
            ['active','=',true],
            ['pos_ids','=', self.pos_session.config_id[0]]
        ];}
    // On Payment screen, allow electronic payments
    screens.PaymentScreenWidget.include({
        finalize_validation: function(){
            var order = this.pos.get_order();
            if (order.get_client().type_identifier != '07'){
                var pos = this.pos;
                var promotion_list = pos.pos_promotions
                order.num_cupon = promotion_list.filter(promotion => promotion.promotion_type == 'buy_x_get_coupon');
            } else {
                order.num_cupon = false
            }
            this._super();
        }
    });
});