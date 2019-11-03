odoo.define('coupon_promotion.screens', function (require) {
    "use strict";
    var screens = require('point_of_sale.screens');
    var PopupWidget = require('point_of_sale.popups');
    var ScreenWidget = screens.ScreenWidget;


    screens.PaymentScreenWidget.include({
        init: function(parent, options) {
            var self = this;
            this._super(parent, options);
            this.keyboard_keydown_handler = function(event){
                if (event.keyCode === 8 || event.keyCode === 46) {
                    event.preventDefault();
                    self.keyboard_handler(event);
                }
            };
            this.keyboard_handler = function(event){
                if (!self.gui.has_popup() && self.pos.get_order().selected_paymentline.get_coupon()){
                    debugger;
                    return;
                }
                var key = '';
                if (event.type === "keypress") {
                    if (event.keyCode === 13) { // Enter
                        self.validate_order();
                    } else if ( event.keyCode === 190 || // Dot
                                event.keyCode === 110 ||  // Decimal point (numpad)
                                event.keyCode === 188 ||  // Comma
                                event.keyCode === 46 ) {  // Numpad dot
                        key = self.decimal_point;
                    } else if (event.keyCode >= 48 && event.keyCode <= 57) { // Numbers
                        key = '' + (event.keyCode - 48);
                    } else if (event.keyCode === 45) { // Minus
                        key = '-';
                    } else if (event.keyCode === 43) { // Plus
                        key = '+';
                    }else{
                        return;
                    }
                } else { // keyup/keydown
                    if (event.keyCode === 46) { // D77elete
                        key = 'CLEAR';
                    } else if (event.keyCode === 8) { // Backspace
                        key = 'BACKSPACE';
                    }
                }
                self.payment_input(key);
            };
        },
        click_paymentmethods: function (id) {
            var cashregister = this.pos.cashregisters.filter(x => x.journal.id===id)[0]
            if (!cashregister.journal.coupons) {
                return this._super(id)
            }
            var self = this;
            if (
                self.pos.get_order().paymentlines.some(
                    x => x.get_coupon()
                )
            ){
                self.gui.show_popup('error',{
                    'title': "Error",
                    'body': 'Solo puede existir un coupon en la Orden',
                });
            }else{
                this.gui.show_popup('textinput',{
                    'value': '',
                    'title':'Ingrese Cupon',
                    'confirm': function(value) {

                        this.pos.get_order().validate_coupon(value).then(function (amount) {
                            if (!amount[0]){
                                self.pos.get_order().add_cupon_paymentline( cashregister, amount[1], value);
                                self.reset_input();
                                self.render_paymentlines();
                            }else{
                                self.gui.show_popup('error',{
                                    'title': "Error",
                                    'body':  amount[0],
                                });
                            }
                        });
                    }
                });
            }
        },
    });
})
