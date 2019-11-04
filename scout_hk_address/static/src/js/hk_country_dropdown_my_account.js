odoo.define('scout_hk_address.hk_portal', function (require) {
'use strict';
var ajax = require('web.ajax');

require('web.dom_ready');
	
	if ($('.o_portal_details').length) {
	    var state_options = $("select[name='state_id']:enabled option:not(:first)");
	    $('.o_portal_details').on('change', "select[name='country_id']", function () {
	        var select = $("select[name='state_id']");
	        var country_id = $("select[name='country_id']");
	        state_options.detach();
	        var displayed_state = state_options.filter("[data-country_id="+($(this).val() || 0)+"]");
	        var nb = displayed_state.appendTo(select).show().size();
	        select.parent().toggle(nb>=1);
	        ajax.jsonRpc('/hk/country_infos','call',{'country': $(this).val()})
	        	.then(function (data) {
	        		if(data){
	        			$("label[for='street']").text("Flat and Floor numbers");
	        			$(".my_street2").removeClass('d-none');
	        			$(".div_name_building").removeClass('d-none');
    	        		$(".div_territories").removeClass('d-none');
//	        			$("select[name='state_id']").parent().hide()
//	        			$("input[name='city']").parent().hide()
//	        			$(".div_town").removeClass('d-none');
//		        		$(".div_district").removeClass('d-none');
//		        		$(".my_city_id").removeClass('d-none');
	        		}else{
	        			$("label[for='street']").text("Street");
	        			$(".my_street2").addClass('d-none');
	        			$(".div_name_building").addClass('d-none');
    	        		$(".div_territories").addClass('d-none');
//	        			$("select[name='state_id']").parent().show()
//	        			$("input[name='city']").parent().show()
//	        			$(".div_town").addClass('d-none');
//		        		$(".div_district").addClass('d-none');
//		        		$(".my_city_id").addClass('d-none');
	        		}
	        		
	        	});
	    });
	    $('.o_portal_details').find("select[name='country_id']").change();
	}
});