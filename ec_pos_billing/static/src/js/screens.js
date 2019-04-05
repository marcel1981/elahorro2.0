odoo.define('ec_pos_billing.screens', function (require) {
"use strict";

var screens = require('point_of_sale.screens');
var core = require('web.core');
var QWeb = core.qweb;
var _t = core._t;
var rpc = require('web.rpc');

screens.ClientListScreenWidget.include({
    save_client_details: function(partner) {
        var self = this;
        var fields = {};
        this.$('.client-details-contents .detail').each(function(idx,el){
			fields[el.name] = el.value;
		});
        var type_id = fields.type_identifier;
        if (fields.identification) {
            if (type_id == '05' || type_id == '04'){
                if (!this.validar_ci_ruc(fields.identification, type_id)){
                    this.gui.show_popup('error',{
                            'title': _t('Error: Could not Save Changes'),
                            'body': "Identificación incorrecta",
                    });
                    return;
			    }
            }

		}else {
            this.gui.show_popup('error',{
            			'title': _t('Error: Could not Save Changes'),
            			'body': "Ingrese identficación",
            		});
            return;
        }

        if(!fields.street){
          this.gui.show_popup('error',{
              'title': _t('Error: Could not Save Changes'),
              'body': "Ingrese la dirección",
          });
          return;
        }

        if(!fields.name){
          this.gui.show_popup('error',{
              'title': _t('Error: Could not Save Changes'),
              'body': "Ingrese un cliente",
          });
          return;
        }

        if(fields.email){
            if(!this.validateEmail(fields.email)){
                  this.gui.show_popup('error',{
                      'title': _t('Error: Could not Save Changes'),
                      'body': "Email incorrecta",
                  });
                  return;
            }
        }

        if(fields.phone){
            if(!this.isNumber(fields.phone)){
                  this.gui.show_popup('error',{
                      'title': _t('Error: Could not Save Changes'),
                      'body': "Teléfono incorrecta",
                  });
                  return;
            }
        }

        fields.id = partner.id || false;

        //partner = new Model('res.partner').query(['identifier']).filter([['identifier','=',fields.identifier]]).all();
        var args = [["identification", "=", fields.identification]];
        var id_client = partner.id || false;

        rpc.query({
            model: "res.partner",
            method: "search",
            args: [args],
        }).then(function(partner_id){
         
            if (partner_id.length > 0 && id_client === false ){

                self.gui.show_popup('error',{
                    'title': _t('Error: Could not Save Changes'),
                    'body': _t('Ya existe un cliente con esa identidicación.'),
                });

            }else {
                rpc.query({
                    model: 'res.partner',
                    method: 'create_from_ui',
                    args: [fields]
                }).then(function(partner_id){
                    self.saved_client_details(partner_id);
                }, function(err_type, err){
                    if (err.data.message) {
                        self.gui.show_populop('error',{
                            'title': _t('Error: Could not Save Changes'),
                            'body': err.data.message,
                        });
                    }else{
                        self.gui.show_popup('error',{
                            'title': _t('Error: Could not Save Changes'),
                            'body': _t('Your Internet connection is probably down.'),
                        });
                    }
                });

            }
        });
    },

    validar_ci_ruc: function(identifier, type){
        var longitud = identifier.length;
         if (identifier !== "" && longitud === 10 && type === '05' ){
             if ( this.check_identifier(identifier) ){
                 return true;
             }
             return false;

         }else if (identifier !== "" && longitud === 13 && type === '04' ) {
             var end_id = identifier.substring(10, longitud);
             if (end_id != '000'){
                 if ( this.check_identifier(identifier) ){
                     return true;
                 }
                 return false;
             }
             return false;
         }
         return false;
	},
    check_identifier(identifier){
        var total = 0;
        var longitud = identifier.length;
        var longcheck = longitud - 1;
        var i;
        var typeDoc = '0';
        var num_prov = 25;


        if (!(parseInt(identifier.substring(0,2)) > 0 && parseInt(identifier.substring(0,2)) < num_prov)){
            return false;
        }  // verifica provincia

        if (identifier.charAt(2) >= 0 && identifier.charAt(2) < 6) {
              typeDoc = '0'

        } else if (parseInt(identifier.charAt(2)) == 6 && identifier.substring(10, 13) != '000') {
              return true;
        } else if (parseInt(identifier.charAt(2)) == 9 && identifier.substring(10, 13) != '000') {
              return true;
        } else    {
            return false;
        }

      var id = identifier.substring(0, 11);
      for(i = 0; i < longcheck; i++){
        if (i%2 === 0) {
          var aux = id.charAt(i) * 2;
          if (aux > 9) aux -= 9;
          total += aux;
        } else {
          total += parseInt(id.charAt(i));
        }
      }

      total = total % 10 ? 10 - total % 10 : 0;

      if (id.charAt(id.length-1) == total) {
          return true;
      }else{
          return false;
      }
    },


   validateEmail(email) {
        var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(email);
    },

    isNumber(number) {
        var pattern = /^\d+$/;
        return pattern.test(number);  // returns a boolean
    },


});

screens.ReceiptScreenWidget.include({
    get_receipt_render_env: function() {
        var order = this.pos.get_order();
        var accessKey =  'No generada';
        var selfOrder = this;
        if (order.get_total_with_tax() > 0 && order.to_invoice){
            rpc.query({
                model: "pos.order",
                method: "getAccessKey",
                args: [[order.name]]
                }).then(function(a){
                   //console.log(a);
                   accessKey = a;
                   order['accessKey'] = accessKey;
		            selfOrder.$el.find('.test').remove();
		            var ker1 = a.slice(0, 40);
		            var ker2 = a.slice(40, 49);
		            selfOrder.$el.find('#key').append('<span>'+ker1+'</span>'+'</br><span>'+ker2+'</span>');
                 });
        }else{
            selfOrder.$el.find('#key').append('<span>No generada</span>');
        }
        return  {   widget: this,
                    pos: this.pos,
                    order: order,
                    receipt: order.export_for_printing(),
                    orderlines: order.get_orderlines(),
                    paymentlines: order.get_paymentlines(),
                    accessKey:accessKey.accessKey,
                    key:accessKey ,
                };
    }
});


});
