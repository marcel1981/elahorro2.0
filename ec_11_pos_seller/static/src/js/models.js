odoo.define('ec_11_pos_seller', function (require) {
    "use strict";
    var core = require('web.core');
    var QWeb = core.qweb;
    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var pos_model = require('point_of_sale.models');
    var _t = core._t;

    pos_model.load_fields("pos.config", ['pos_location_id'], ['point_of_sale'])

    pos_model.load_models({
        model: 'pos.salesman',
        fields: ['name', 'identification', 'barcode', 'location'],
        domain: function (self) {
            return [['location', '=', self.config.pos_location_id[0]]];
        },
        loaded: function (self, pos_salesmans) {
            self.pos_salesmans = pos_salesmans;
            self.pos_salesmans_by_id = {};
            for (var i = 0; i < pos_salesmans.length; i++) {
                self.pos_salesmans_by_id[pos_salesmans[i].id] = pos_salesmans[i];
            }
        },
    });

      pos_model.load_models({
        model: 'account.journal',
        fields: ['isJournalCreditNote'],
        loaded: function (self, journal_payment) {
            self.journal_payment = journal_payment;
            self.journal_payment_by_id = {};
            for (var i = 0; i < journal_payment.length; i++) {
                self.journal_payment_by_id[journal_payment[i].id] = journal_payment[i];
            }
        },
    });

    var OrderSuper = pos_model.Order;
    var _super_order = pos_model.Order.prototype;
    pos_model.Order = pos_model.Order.extend({
        /*initialize: function(attr, options) {
            _super_order.initialize.call(this,attr,options);
            this.pos_salesman_id = this.pos_salesman_id || false;

        },*/
        export_as_JSON: function () {
            var res = OrderSuper.prototype.export_as_JSON.call(this);
            if (this.vendedora_id) {
                res['vendedora_id'] = this.vendedora_id;
            }

            if (this.accessKey) {
                res['accessKey'] = this.accessKey;
            }

            return res;
        },
        get_vendedora_id: function (vendedora_id) {
            var res = this.pos.pos_salesmans_by_id[vendedora_id];
            var vname = "";
            if (res){
                vname = res.name;
            }

            return vname;
        },

        exist_seller: function () {
            if (this.vendedora_id){
                return true;
            }
            return false;
        },


    });

    //evento click boton pos salesman
    screens.PaymentScreenWidget = screens.PaymentScreenWidget.include({
        renderElement: function () {
            var self = this;
            this._super()

            this.$('.js_set_pos_salesman').click(function (e) {
                self.gui.show_screen('vendedorlist')
            });
            console.log(self);

            var order = this.pos.get_order();
            order.set_to_invoice(!order.is_to_invoice());

            this.$('.js_invoice').addClass('highlight');
        },
        order_is_valid: function(force_validation) {
            var self = this;
            var res = this._super(force_validation);
            var order = self.pos.get_order();

            var totalAmountOrder = order.get_total_with_tax();
            var payment;
            var isPaymentCreditNote  = false;
            var amountTotalPayment = 0;
            for (payment = 0; payment < order.paymentlines.models.length; payment++){
                if (order.paymentlines.models[payment].amount == 0 ){
                     this.gui.show_popup('error',{
                            'title': _t('Error: Could not Save Changes'),
                            'body': "El método de pago es incorrecto debe ser mayor a cero",
                      });
                     return;
                 }
                if (order.paymentlines.models[payment].cashregister.journal.type != 'cash' ) {
                     amountTotalPayment += order.paymentlines.models[payment].amount;
                }

                var journal_id = self.pos.journal_payment.find(obj => obj.id == order.paymentlines.models[payment].cashregister.journal.id);
                if (journal_id.isJournalCreditNote) {
                     isPaymentCreditNote = true;
                }

            }

            if (totalAmountOrder < 0 && !isPaymentCreditNote ){
                 this.gui.show_popup('error',{
            			'title': _t('Error: Could not Save Changes'),
            			'body': "El método de pago es incorrecto seleccione nota de crédito",
                  });
                 return;
            }


            if (!order.attributes.client){
                 this.gui.show_popup('error',{
            			'title': _t('Error: Could not Save Changes'),
            			'body': "Orden sin cliente",
                  });
                 return;

            }

            if (parseInt(amountTotalPayment.toFixed(2)) > parseInt(totalAmountOrder.toFixed(2))){
                 this.gui.show_popup('error',{
            			'title': _t('Error: Could not Save Changes'),
            			'body': "Error al registrar los pagos",
                  });
                 return;

            }

            if (!order.exist_seller()){
                 this.gui.show_popup('error',{
            			'title': _t('Error: Could not Save Changes'),
            			'body': "Seleccione Vendedor",
                  });
                 return;

            }

            return res;
        },
        get_total_exento:function(){
            var taxes =  this.pos.taxes;
            var exento = 0;
            this.orderlines.each(function(line){

                var product =  line.get_product();
                var taxes_ids = product.taxes_id;
                _(taxes_ids).each(function(el){
                    _.detect(taxes,function(t){
                        if(t.id === el && t.amount === 0){
                            exento += (line.get_unit_price() * line.get_quantity());
                        }
                    });
                });
            });
            return exento;
        },
    });

    //crear screen para seleccionar vendedoras
    var VendedorasListScreenWidget = screens.ScreenWidget.extend({
        template: 'VendedorasListScreenWidget',

        init: function (parent, options) {
            this._super(parent, options);
        },

        auto_back: true,

        show: function () {
            var self = this;
            this._super();

            this.renderElement();

            this.$('.back').click(function () {
                self.gui.back();
            });


            var vendedoras = this.pos.pos_salesmans;
            this.render_list(vendedoras);

            this.$('.vendedoras-list-contents').delegate('.client-line', 'click', function (event) {
                self.line_select(event, $(this), parseInt($(this).data('id')));
            });

            var search_timeout = null;

            if (this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard) {
                this.chrome.widget.keyboard.connect(this.$('.searchbox input'));
            }

            this.$('.searchbox input').on('keypress', function (event) {
                clearTimeout(search_timeout);

                var searchbox = this;

                search_timeout = setTimeout(function () {
                    self.perform_search(searchbox.value, event.which === 13);
                }, 70);
            });

            this.$('.searchbox .search-clear').click(function () {
                self.clear_search();
            });
        },

        perform_search: function (query, result) {
            if (query) {
                var vendedoras_aux = this.search_vendedoras(query)
                if (vendedoras_aux.length > 0) {
                    this.render_list(vendedoras_aux)
                }

            }else{
                this.render_list(this.pos.pos_salesmans)
            }

        },

        search_vendedoras: function (query) {
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g, '.');
                query = query.replace(/ /g, '.+');
            } catch (e) {
                return [];
            }
            var results = [];
            var items_v = this.pos.pos_salesmans;


            var filtered_by_name = _.filter(items_v, function (item_v) {
                return item_v.name.toLowerCase().indexOf(query.toLowerCase()) > -1
            });

            var filtered_by_barcode = _.filter(items_v, function (item_v) {
                return item_v.barcode.indexOf(query) > -1
            });

            var filtered_by_identif = _.filter(items_v, function (item_v) {
                return item_v.identification.indexOf(query) > -1
            });

            if (filtered_by_barcode.length > 0) {
                results.push(filtered_by_barcode[0])
            }

            if (filtered_by_identif.length > 0) {
                results.push(filtered_by_identif[0])
            }
            if (filtered_by_name.length > 0) {
                results.push(filtered_by_name[0])
            }

            return results;
        },


        hide: function () {
            this._super();
            this.new_client = null;
        },

        clear_search: function () {
            var vendedoras = this.pos.pos_salesmans;
            this.render_list(vendedoras);
            this.$('.searchbox input')[0].value = '';
            this.$('.searchbox input').focus();
        },
        render_list: function (vendedoras) {
            var contents = this.$el[0].querySelector('.vendedoras-list-contents');
            contents.innerHTML = "";
            for (var i = 0, len = Math.min(vendedoras.length, 1000); i < len; i++) {
                var vendedora = vendedoras[i];
                var vendedoralineHTML = QWeb.render('VendedoraLine', {widget: this, vendedora: vendedora});
                var vendedora_line = document.createElement('tbody');
                vendedora_line.innerHTML = vendedoralineHTML;
                vendedora_line = vendedora_line.childNodes[1];
                contents.appendChild(vendedora_line);
            }
        },


        line_select: function (event, $line, id) {
            var vendedora = this.pos.pos_salesmans_by_id[id];
            this.pos.gui.screen_instances.payment.$el.find(".js_set_pos_salesman span").html(vendedora.name)
            var order = this.pos.get('selectedOrder');
            order['vendedora_id'] = vendedora.id;
            this.pos.gui.show_screen('payment');
            //alert(vendedora)
        },


        close: function () {
            this._super();
            if (this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard) {
                this.chrome.widget.keyboard.hide();
            }
        },
    });
    gui.define_screen({name: 'vendedorlist', widget: VendedorasListScreenWidget});

});
