$(document).ready(function () {
	odoo.define('scout_baazar.website_side', function (require) {
    "use strict";
    var ajax = require('web.ajax');
	var aaa=$('#school_id')
		$(aaa).select2({placeholder: 'Select an option'});
	});
	
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

});