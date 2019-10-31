odoo.define('coupon_promotions.models', function (require) {
    "use strict";
    var utils = require('web.utils');
    var models = require('point_of_sale.models');
    var rpc = require('web.rpc');
    var modules = models.PosModel.prototype.models;
    var round_di = utils.round_decimals;
    for(var i=0; i<modules.length; i++){
        var model=modules[i];
        if(model.model === 'account.journal'){
            model.fields.push('iscoupon');
        }
    }
    var _paylineproto = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        init_from_JSON: function (json) {
            _paylineproto.init_from_JSON.apply(this, arguments);
            this.coupon = json.coupon;
        },
        export_as_JSON: function () {
            var json = _paylineproto.export_as_JSON.apply(this,arguments);
            json.coupon = this.coupon;
            return json;
        },
        set_coupon: function(value){
            this.order.assert_editable();
            this.coupon = value;
            this.trigger('change',this);
        },
        get_coupon: function(){
            return this.coupon
        },
    })
    models.Order = models.Order.extend({
        validate_coupon: function(coupon) {
            return rpc.query({
                model: 'coupon.promotion',
                method: 'validate_coupon',
                args: [
                    coupon,
                    this.pos.get_client().id,
                    this.pos.config.crm_team_id[0]

                ]
            })
        },
        add_cupon_paymentline: function(cashregister,amount, coupon) {
            this.assert_editable();
            var newPaymentline = new models.Paymentline({},{order: this, cashregister:cashregister, pos: this.pos});
            newPaymentline.set_amount(amount);
            newPaymentline.set_coupon(coupon);
            this.paymentlines.add(newPaymentline);
            this.select_paymentline(newPaymentline);
        },
    })
})