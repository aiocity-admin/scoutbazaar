odoo.define('scout_stock.checkout_paynow', function (require) {
    'use strict';

    require('web.dom_ready');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var i = require('website_sale_delivery.checkout');

    /* Handle interactive carrier choice + cart update */
    var $pay_button = $('#o_payment_form_pay');
    console.log('=========$pay_button==================',$pay_button)
    var line_msg = $('#add_line_msg .delivery_msg');
    console.log('=========line_msg==================',line_msg)
    if (line_msg){
    	$pay_button.addClass('d-none');
    }
    if(line_msg.length == 0){
    	$pay_button.removeClass('d-none');
    }
});
