odoo.define('scout_vendor.vendor_international_shipping', function (require) {
    'use strict';
    var ajax = require('web.ajax');
    $(document).ready(function(){
    	var int_shippping = $("input.vendor_int_shippping")
    	int_shippping.change(function(e){
    		var self = this;
    		var delivery_id = $(this).attr('id')
    		var country_code = $(this).attr('name').split('int_ship_vendor')[1]
    		ajax.jsonRpc('/calculate/vendor/international_shipping','call',{'vendor_delivery_id':delivery_id,'vendor_country_code':country_code})
    		.then(function(vals){
    			if(vals['error_message']){
    				$(self).parent().parent().find('.vendor_delivery_price').text(' ')
    				$(self).parent().find('.vendor_delivery_price').text(vals['error_message'])
    				location.reload();
    			}
    			else{
    				$(self).parent().parent().find('.vendor_delivery_price').text(' ')
    				$(self).parent().find('.vendor_delivery_price').text(vals['vendor_delivery_price'])
    				location.reload();
    			}
    		})
    	})
    })
})