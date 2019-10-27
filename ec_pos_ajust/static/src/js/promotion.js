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

    var OrderSuper = models.Order;
    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        export_as_JSON: function () {
            debugger;
            var res = OrderSuper.prototype.export_as_JSON.call(this);
                res['promotion_list'] = this.num_cupon;
            return res
            }
    });
    screens.PaymentScreenWidget.include({
        finalize_validation: function(){
            var order = this.pos.get_order();
            var promotion_list = this.pos.pos_promotions;
            if (order.get_client().type_identifier != '07'){
                order.num_cupon = []
                for (var promotion in promotion_list){
                    if (promotion_list[promotion].promotion_type == 'buy_x_get_coupon'){
                        for (var num in Array.from(Array(Math.floor(order.get_total_with_tax()/promotion_list[promotion].value_per_coupon) + 1).keys()).slice(1)){
                            order.num_cupon.push({
                                promotion_id: promotion_list[promotion].id,
                                name_raffle : promotion_list[promotion].name_raffle,
                                date_raffle: promotion_list[promotion].date_raffle,
                                from_date : promotion_list[promotion].from_date,
                                to_date: promotion_list[promotion].to_date,
                                promotion_code: promotion_list[promotion].promotion_code,
                                seq: this.pos.config.name + '-'
                                        + promotion_list[promotion].promotion_code +'-'
                                        + moment(new Date()).locale('en').format("YYYYMMDDHHmmss")
                            })
                        }
                    }
                }
            }
            this._super();
        }
    });
});