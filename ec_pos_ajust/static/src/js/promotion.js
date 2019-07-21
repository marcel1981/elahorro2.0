odoo.define('ec_pos_ajust.promotion', function (require) {
"use strict";

    var screens = require('point_of_sale.screens');
	var models = require('point_of_sale.models');
    var pos_promotion = models.PosModel.prototype.models.filter(x => x.model =='pos.promotion')[0];
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
            }
            this._super();
        }
    });
});