odoo.define('scout_vendor.vendor_international_shipping', function (require) {
    'use strict';
    var ajax = require('web.ajax');
    $(document).ready(function(){
    	var int_shippping = $("input.vendor_int_shippping")
//    	
//    	var shipping_length = int_shippping.length
//    	var count = 0
//        	
//    	if(int_shippping.length > 0){
//	    	$.blockUI({ 
//				message: '<span>Please wait, we are getting best price for you! </span>'
//			});
//    	}
//    	
    	
//    	$.each( int_shippping, function( key, value ) {
//    		var self = this;
//    		var delivery_idi = $(value).attr('id')
//    		var country_codei = $(value).attr('name').split('int_ship_vendor')[1]
//    		
//    		ajax.jsonRpc('/my/calculate/vendor/international_shipping','call',{'vendor_delivery_idi':delivery_idi,'vendor_country_codei':country_codei})
//    		.then(function(vals){
//    			if(vals['error_message']){
//    				$(self).parent().find('.vendor_delivery_price').text(' ')
//    				count += 1;
//					if(count == shipping_length){
//						$.unblockUI();
//					}
////    				$(self).parent().find('.vendor_delivery_price').text(vals['error_message'])
//    			}
//    			else{
//    				$(self).parent().find('.vendor_delivery_price').text(' ')
//    				$(self).parent().find('.vendor_delivery_price').text(vals['vendor_delivery_pricei'])
//    				count += 1;
//					if(count == shipping_length){
//						$.unblockUI();
//					}
//    			}
//    		})
//    	});
    	int_shippping.change(function(e){
    		var self = this;
    		var delivery_id = $(this).attr('id')
    		var country_code = $(this).attr('name').split('int_ship_vendor')[1]
    		$.blockUI({ 
				message: '<span>Please wait, we are getting best price for you! </span>'
				});
//    		var my_delivery_price = $(self).parent().find('.vendor_delivery_price').text()
    		ajax.jsonRpc('/calculate/vendor/international_shipping','call',{'vendor_delivery_id':delivery_id,'vendor_country_code':country_code})
    		.then(function(vals){
    			if(vals['error_message']){
    				$(self).parent().find('.vendor_delivery_price').text(vals['error_message'])
    				
    			}
    			else{
    				var main_parent = $('#cart_products').parent().parent().parent().parent()
    				$(main_parent).empty();
    				$(main_parent).append(vals['website_sale.cart_summary']);
    				$('.vendor_amount_delivery').text(vals['vendor_amount_delivery'])
    				$.unblockUI();
//    				$(self).parent().find('.vendor_delivery_price').text(vals['vendor_delivery_price'])
    			}
    		})
    	})
    })
})