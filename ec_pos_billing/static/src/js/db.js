odoo.define('ec_pos_billing.DB', function (require) {
"use strict";

var DB = require('point_of_sale.DB');

DB.include({
    _partner_search_string: function(partner){
        var str =  partner.name;
        if(partner.identification){
            str += '|' + partner.identification;
            str += '|' + partner.identification.replace('.','');
        }
        if(partner.barcode){
            str += '|' + partner.barcode;
        }
        if(partner.address){
            str += '|' + partner.address;
        }
        if(partner.phone){
            str += '|' + partner.phone.split(' ').join('');
        }
        if(partner.mobile){
            str += '|' + partner.mobile.split(' ').join('');
        }
        if(partner.email){
            str += '|' + partner.email;
        }
        str = '' + partner.id + ':' + str.replace(':','') + '\n';
        return str;
    },
});


/*DB.include({
    _product_search_string: function(product){
        var str =  '';
        if(product.code){
            str +=  product.code;
        }
        str = str +'\n';
        console.log(str);
        return str;
    },

});*/

});