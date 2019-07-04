odoo.define('ec_pos_ajust.promotion', function (require) {
"use strict";
	var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var pos_promotion = models.PosModel.prototype.models.filter(x => x.model =='pos.promotion')[0];
    pos_promotion.domain = function(self){
        var current_date = moment(new Date()).locale('en').format("YYYY-MM-DD");
        return [
            ['from_date','<=',current_date],
            ['to_date','>=',current_date],
            ['active','=',true],
            ['pos_id','=', self.pos_session.config_id[0]]
        ];}
});