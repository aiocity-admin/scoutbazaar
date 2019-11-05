odoo.define('scout_stock.international_shipping', function (require) {
    'use strict';
    var ajax = require('web.ajax');
    $(document).ready(function(){
    	var int_shippping = $("input.int_shippping")
    	
    	int_shippping.change(function(e){
    		var self = this;
    		var delivery_id = $(this).attr('id')
    		var country_code = $(this).attr('name').split('int_ship_')[1]
    		console.log("Callllllled-----------",delivery_id,country_code)
    		ajax.jsonRpc('/calculate/international_shipping','call',{'delivery_id':delivery_id,'country_code':country_code})
    		.then(function(vals){
    			if(vals['error_message']){
    				$(self).parent().parent().find('.delivery_price').text(' ')
    				$(self).parent().find('.delivery_price').text(vals['error_message'])
    			}
    			else{
    				$(self).parent().parent().find('.delivery_price').text(' ')
    				$(self).parent().find('.delivery_price').text(vals['delivery_price'])
    			}
    				
    		})
    	})
    })
    
})