odoo.define('pos_multi_barcode', function (require) {
"use strict";
    var models = require('point_of_sale.models');
    var core = require('web.core');
    var PosDB = require('point_of_sale.DB');
    var screens = require('point_of_sale.screens');
    var _t = core._t;
    models.load_fields('product.product',['pos_multi_barcode']);
    models.load_models([{
        model: 'pos.multi.barcode',
        fields: ['name','product_id'],
        loaded: function(self,result){
            self.db.add_barcode_lst(result);
        },
    }],{'after': 'pos.category'});

    PosDB.include({
        init: function(options){
            var self = this;
            this.product_barcode_list = {};
            this._super(options);

        },
        add_products: function(products){
            var self = this;
            this._super(products); 
            
            for(var i = 0, len = products.length; i < len; i++){
                var product = products[i];
                if(product.pos_multi_barcode){
                    for(var k=0;k<self.product_barcode_list.length;k++){
                        for(var j=0;j<product.pos_multi_barcode.length;j++){
                            if(self.product_barcode_list[k].id == product.pos_multi_barcode[j]){
                                this.product_by_barcode[self.product_barcode_list[k].name] = product;
                            }
                        }
                    }
                }
            }

        },
        add_barcode_lst:function(barcode){
            this.product_barcode_list = barcode;
        },

    });


});

