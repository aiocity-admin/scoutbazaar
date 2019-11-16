odoo.define('scout_vendor.vendor_international_shipping', function (require) {
    'use strict';
    var ajax = require('web.ajax');
    $(document).ready(function(){
    	var int_shippping = $("input.vendor_int_shippping")
    	var pay_now_button1 = $('#o_payment_form_pay')
//    	var error_count = 0
    	
//    	int_shippping.change(function(e){
//    		var self = this;
//    		var delivery_id = $(this).attr('id')
//    		var country_code = $(this).attr('name').split('int_ship_vendor')[1]
//    		$.blockUI({ 
//				message: '<span>Please wait, we are getting best price for you! </span>'
//				});
//    		ajax.jsonRpc('/calculate/vendor/international_shipping','call',{'vendor_delivery_id':delivery_id,'vendor_country_code':country_code})
//    		.then(function(vals){
//    			if(vals['error_message']){
//    				$(self).parent().find('.is_my_error').text(' ')
//    				$(self).parent().find('.is_my_error').text(vals['error_message'])
//    				error_count += 1
//    				$.unblockUI();
//    			}
//    			else{
//    				var main_parent = $('#cart_products').parent().parent().parent().parent()
//    				$(main_parent).empty();
//    				$(main_parent).append(vals['website_sale.cart_summary']);
//    				$('.vendor_amount_delivery').text(vals['vendor_amount_delivery'])
//    				$.unblockUI();
//    			}
//    		})
//    		console.log('========error_count==========q======',error_count)
//    	});
    })
})