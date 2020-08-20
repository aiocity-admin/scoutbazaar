$(document).ready(function () {
	odoo.define('scout_baazar.website_side', function (require) {
    "use strict";
    var ajax = require('web.ajax');
    var utils = require('web.utils');
	var aaa=$('#school_id')
		$(aaa).select2({placeholder: 'Select an option'});

		$('.as-search form input').addClass("search_shop")
		$('.search_shop').on('keydown, keyup', function () {
	  		var texInputValue = $('.search_shop').val();
	  		if ($(texInputValue)){
	  			utils.set_cookie('search', true);
	  		}
		});
		if ($(utils.get_cookie('search'))){
			if ($('.row .oe_product_cart').length == 0){
				$('.s_carousel_default').hide()
			}
		}
	});
	
//    add addition note==========
    var pay_now_button = $('button#o_payment_form_pay')
    var addition_note_text = $('#additional_note_area')
    var addition_note_order = $('input[name="additional_note_order"]')
	if(pay_now_button && addition_note_text && addition_note_order){
		$(pay_now_button).click(function(){
		    ajax.jsonRpc('/set/additional/note','call',{'note':$(addition_note_text).val(),'order':$(addition_note_order).val()}).then(function(){
		    	
		    })
		});
	}
//    ajax.jsonRpc('/find/same_nso_product','call',{}).then(function(){
//    })
	
	
	var c_id = $('#keep_shop_all_category')
	if (c_id){
		c_id.click(function(){
		    ajax.jsonRpc('/get/shop/url','call',{}).then(function(){
		    	
		    })
		});
	}

	// Product filter scout program wise

	$("#products_grid_before .js_attributes .clear_program_filter").on("click", function(e){
		$("input[name='scout_program']").each(function(){
             $(this).prop("checked", false);
        });
		$("form.js_attributes").submit();
	});

	$("input[name='scout_program']").on("click", function(e){
	$("input[name='scout_program']").each(function(){
        $(this).prop("checked", false);
    });
	    $(this).prop("checked", true);
        $("form.js_attributes").submit();
	});

	// if (window.location.href.indexOf('/shipping_policy') > -1) {
	// 	$('.page_headers').css("font-family", "inherit")
	// 	$('.s_title_default').css("font-family", "inherit")
	// 	$('.textrun span' ).css("line-height", "1.4")
	// 	$('div .offset-lg-1').css("line-height", "1.2")
	// 	$('.MsoNormal span').css("font-family", "Roboto", "Noto") 
	// }
	// if (window.location.href.indexOf('/refund_policy') > -1) {
	// 	$('.page_headers').css("font-family", "inherit")
	// 	$('.s_title_default').css("font-family", "inherit")
	// 	$('.textrun span' ).css("line-height", "1.4")
	// 	$('div .offset-lg-1').css("line-height", "1.2")
	// 	$('.MsoNormal span').css("font-family", "Roboto", "Noto") 
	// }
	// if (window.location.href.indexOf('/term_of_use') > -1) {
	// 	$('.page_headers').css("font-family", "inherit")
	// 	$('.s_title_default').css("font-family", "inherit")
	// 	$('.textrun span' ).css("line-height", "1.4")
	// 	$('div .offset-lg-1').css("line-height", "1.4")
	// 	$('.MsoNormal span').css("font-family", "Roboto", "Noto") 
	// 	$('.offset-lg-1 h1').css("font-family", "inherit")
	// }	
	// if (window.location.href.indexOf('/privacy') > -1) {
	// 	$('.page_headers').css("font-family", "inherit")
	// 	$('.s_title_default').css("font-family", "inherit")
	// 	$('.textrun span' ).css("line-height", "1.4")
	// 	$('div .offset-lg-1').css("line-height", "1.4")
	// 	$('.MsoNormal span').css("font-family", "Roboto", "Noto") 
	// 	$('.offset-lg-1 h1').css("font-family", "inherit")
	// }

	
});