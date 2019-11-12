odoo.define('scout_vendor.vendor_international_shipping', function (require) {
    'use strict';
    var ajax = require('web.ajax');
    $(document).ready(function(){
    	var int_shippping = $("input.vendor_int_shippping")
    	var self = this;
    	$.each( int_shippping, function( key, value ) {
    		var self = this;
    		var delivery_idi = $(value).attr('id')
    		var country_codei = $(value).attr('name').split('int_ship_vendor')[1]
    		ajax.jsonRpc('/my/calculate/vendor/international_shipping','call',{'vendor_delivery_idi':delivery_idi,'vendor_country_codei':country_codei})
    		.then(function(vals){
    			console.log('=====================================',vals)
    			if(vals['error_message']){
    				$(self).parent().find('.vendor_delivery_price').text(' ')
    				$(self).parent().find('.vendor_delivery_price').text(vals['error_message'])
    			}
    			else{
    				$(self).parent().find('.vendor_delivery_price').text(' ')
    				$(self).parent().find('.vendor_delivery_price').text(vals['vendor_delivery_pricei'])
    			}
    		})
    	});
    	int_shippping.change(function(e){
    		var self = this;
    		var delivery_id = $(this).attr('id')
    		var country_code = $(this).attr('name').split('int_ship_vendor')[1]
    		var my_delivery_price = $(self).parent().find('.vendor_delivery_price').text()
    		console.log("Callllllled-----------",delivery_id,country_code,my_delivery_price)
    		ajax.jsonRpc('/calculate/vendor/international_shipping','call',{'vendor_delivery_id':delivery_id,'vendor_country_code':country_code,'my_delivery_price':my_delivery_price})
    		.then(function(vals){
    			if(vals['vendor_delivery_price']){
    				$(self).parent().find('.vendor_delivery_price').text(vals['vendor_delivery_price'])
    				location.reload();
    			}
    		})
    	})
    })
})