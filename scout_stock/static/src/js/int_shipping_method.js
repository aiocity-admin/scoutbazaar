odoo.define('scout_stock.international_shipping', function (require) {
    'use strict';
    var ajax = require('web.ajax');
    $(document).ready(function(){
    	var int_shippping = $("input.int_shippping")
    	
    	
    	
		$.each( int_shippping, function( key, value ) {
		var self = this;
		var delivery_id = $(value).attr('id')
		var country_code = $(value).attr('name').split('int_ship_')[1]
		
		ajax.jsonRpc('/get/nso_international_shipping_rates','call',{'nso_delivery_id':delivery_id,'nso_country_code':country_code})
			.then(function(vals){
				if(vals['error_message']){
					$(self).parent().find('.delivery_price').text(' ')
//					$(self).parent().find('.delivery_price').text(vals['error_message'])
				}
				else{
					$(self).parent().find('.delivery_price').text(' ')
					$(self).parent().find('.delivery_price').text(vals['nso_delivery_price'])
				}
			})
    	})
    	
    	
    	int_shippping.change(function(e){
    		var self = this;
    		var delivery_id = $(this).attr('id')
    		var country_code = $(this).attr('name').split('int_ship_')[1]
    		$.blockUI({ 
    				message: '<span>Please wait, we are getting best price for you! </span>'
    				});
    		ajax.jsonRpc('/calculate/international_shipping','call',{'delivery_id':delivery_id,'country_code':country_code})
    		.then(function(vals){
    			if(vals['error_message']){
    				console.log("Error--------------")
//    				$(self).parent().parent().find('.delivery_price').text(' ')
//    				$(self).parent().find('.delivery_price').text(vals['error_message'])
//    				location.reload();
    			}
    			else{
    				var main_parent = $('#cart_products').parent().parent().parent().parent()
    				$(main_parent).empty();
    				$(main_parent).append(vals['website_sale.cart_summary']);
    				$('.nso_amount_delivery').text(vals['nso_amount_delivery'])
    				$.unblockUI();
//    				$(self).parent().parent().find('.delivery_price').text(' ')
//    				$(self).parent().find('.delivery_price').text(vals['delivery_price'])
//    				location.reload();
    			}
    				
    		})
    	})
    })
    
})