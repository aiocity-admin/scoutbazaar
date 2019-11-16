odoo.define('scout_stock.international_shipping', function (require) {
    'use strict';
    var ajax = require('web.ajax');
    $(document).ready(function(){
    	var int_shippping = $("input.int_shippping")
    	var int_vendor_shippping = $("input.vendor_int_shippping")
    	var shipping_length =0
    	var count = 0
    	var error_count = 0
    	var vendor_domestic_error = $('.is_vendor_error_domestic')
    	var nso_domestic_error = $('.is_nso_error_domestic')
    	var pay_now_button = $('#o_payment_form_pay')
    	
    	if(int_shippping.length > 0){
    		shipping_length += int_shippping.length
	    	$.blockUI({ 
				message: '<span>Please wait, we are getting best price for you! </span>'
			});
    	}
    	
    	if(int_vendor_shippping.length > 0){
    		shipping_length += int_vendor_shippping.length
	    	$.blockUI({ 
				message: '<span>Please wait, we are getting best price for you! </span>'
			});
    	}
    	
    	//NSO===========================================
		$.each( int_shippping, function( key, value ) {
		var self = this;
		var delivery_id = $(value).attr('id')
		var country_code = $(value).attr('name').split('int_ship_')[1]
		
		ajax.jsonRpc('/get/nso_international_shipping_rates','call',{'nso_delivery_id':delivery_id,'nso_country_code':country_code})
			.then(function(vals){
				if(vals['error_message']){
					$(self).parent().find('.is_nso_error').text(' ')
    				$(self).parent().find('.is_nso_error').text(vals['error_message'])
    				$(self).parent().find('.delivery_price').text('$ 0.0')
    				error_count += 1
					count += 1;
					if(count == shipping_length){
						$.unblockUI();
					}
					if ($(self).is(":checked")){
    					pay_now_button.prop("disabled", true);
    				}
				}
				else{
					$(self).parent().find('.delivery_price').text(vals['nso_delivery_price'])
					count += 1;
					if(count == shipping_length){
						$.unblockUI();
					}
				}
				
			})
    	});
    	
    	//Vendor===========================================
    	$.each( int_vendor_shippping, function( key, value ) {
    		var self = this;
    		var delivery_idi = $(value).attr('id')
    		var country_codei = $(value).attr('name').split('int_ship_vendor')[1]
    		
    		ajax.jsonRpc('/my/calculate/vendor/international_shipping','call',{'vendor_delivery_idi':delivery_idi,'vendor_country_codei':country_codei})
    		.then(function(vals){
    			if(vals['error_message']){
    				$(self).parent().find('.is_my_error').text(' ')
    				$(self).parent().find('.is_my_error').text(vals['error_message'])
    				$(self).parent().find('.vendor_delivery_price').text('$ 0.0')
    				error_count += 1;
    				count += 1;
					console.log('=============is checked=====',$(self).is(":checked"))
    				if(count == shipping_length){
						$.unblockUI();
					}
					if ($(self).is(":checked")){
    					pay_now_button.prop("disabled", true);
    				}
    			}
    			else{
    				$(self).parent().find('.vendor_delivery_price').text(vals['vendor_delivery_pricei'])
    				count += 1;
					if(count == shipping_length){
						$.unblockUI();
					}
    			}
    		})
    	});
    	
		//NSO===========================================
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
    				$(self).parent().find('.is_nso_error').text(' ')
    				$(self).parent().find('.is_nso_error').text(vals['error_message'])
//    				$(self).parent().parent().find('.delivery_price').text('$ 0.0')
    				error_count += 1
    				if ($(self).is(":checked")){
    					pay_now_button.prop("disabled", true);
    				}
    				$.unblockUI();
    			}
    			else{
    				var main_parent = $('#cart_products').parent().parent().parent().parent()
    				$(main_parent).empty();
    				$(main_parent).append(vals['website_sale.cart_summary']);
    				$('.nso_amount_delivery').text(vals['nso_amount_delivery'])
    				
    				
    				
    				
    				var vendor_radio_checked = int_vendor_shippping
    				var nso_radio_checked = int_shippping
    				var vendor_radio_error = false;
    				var nso_radio_error = false;
    				if (nso_radio_checked.length > 0){
    					_.each(nso_radio_checked,function(value){
    						if($(value).is(":checked")){
    							var check_error_text = $(value).parent().find('.is_nso_error');
    							if (check_error_text.length > 0){
    								nso_radio_error = true
    							}
    						}
    					})
    				}
    				
    				if (vendor_radio_checked.length > 0){
    					_.each(vendor_radio_checked,function(value){
    						if($(value).is(":checked")){
    							var check_error_text = $(value).parent().find('.is_my_error');
    							if (check_error_text.length > 0){
    								vendor_radio_error = true
    							}
    						}
    					})
    				}
    				
    				console.log("Error===============",nso_radio_error,vendor_radio_error)
    				
    				if(nso_radio_error || vendor_radio_error || vendor_domestic_error.length > 0 || nso_domestic_error.length > 0){
    					pay_now_button.prop("disabled", true);
    				}
    				else{
    					pay_now_button.prop("disabled", false);
    				}
    				
    				$.unblockUI();
    			}
    				
    		})
    	});
    	
    	//Vednor===========================================
    	int_vendor_shippping.change(function(e){
    		var self = this;
    		var delivery_id = $(this).attr('id')
    		var country_code = $(this).attr('name').split('int_ship_vendor')[1]
    		$.blockUI({ 
				message: '<span>Please wait, we are getting best price for you! </span>'
				});
    		ajax.jsonRpc('/calculate/vendor/international_shipping','call',{'vendor_delivery_id':delivery_id,'vendor_country_code':country_code})
    		.then(function(vals){
    			if(vals['error_message']){
    				$(self).parent().find('.is_my_error').text(' ')
    				$(self).parent().find('.is_my_error').text(vals['error_message'])
    				$(self).parent().find('.vendor_delivery_price').text('$ 0.0')
    				error_count += 1
    				console.log('=============is checked=====',$(self).is(":checked"))
    				if ($(self).is(":checked")){
    					pay_now_button.prop("disabled", true);
    				}
    				$.unblockUI();
    			}
    			else{
    				var main_parent = $('#cart_products').parent().parent().parent().parent()
    				$(main_parent).empty();
    				$(main_parent).append(vals['website_sale.cart_summary']);
    				$('.vendor_amount_delivery').text(vals['vendor_amount_delivery'])
    				
    				var vendor_radio_checked = int_vendor_shippping
    				var nso_radio_checked = int_shippping
    				var vendor_radio_error = false;
    				var nso_radio_error = false;
    				if (nso_radio_checked.length > 0){
    					_.each(nso_radio_checked,function(value){
    						if($(value).is(":checked")){
    							var check_error_text = $(value).parent().find('.is_nso_error');
    							if (check_error_text.length > 0){
    								nso_radio_error = true
    							}
    						}
    					})
    				}
    				
    				if (vendor_radio_checked.length > 0){
    					_.each(vendor_radio_checked,function(value){
    						if($(value).is(":checked")){
    							var check_error_text = $(value).parent().find('.is_my_error');
    							if (check_error_text.length > 0){
    								vendor_radio_error = true
    							}
    						}
    					})
    				}
    				
    				console.log("Error===============",nso_radio_error,vendor_radio_error)
    				
    				if(nso_radio_error || vendor_radio_error || vendor_domestic_error.length > 0 || nso_domestic_error.length > 0){
    					pay_now_button.prop("disabled", true);
    				}
    				else{
    					pay_now_button.prop("disabled", false);
    				}
    				$.unblockUI();
    			}
    		})
    	});
    	console.log('=========vendor and nso====',vendor_domestic_error.length,nso_domestic_error.length)
		if (vendor_domestic_error.length > 0 || nso_domestic_error.length > 0){
			pay_now_button.prop("disabled", true);
		}
    })
    
})