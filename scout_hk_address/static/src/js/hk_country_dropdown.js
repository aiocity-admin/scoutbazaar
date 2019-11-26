odoo.define('scout_hk_address.hk_country', function (require) {
'use strict';

var utils = require('web.utils');
var ProductConfiguratorMixin = require('sale.ProductConfiguratorMixin');
var core = require('web.core');
var config = require('web.config');
var sAnimations = require('website.content.snippets.animation');
require("website.content.zoomodoo");

var hkCountryOnchage = require('jt_express.ph_country');
var _t = core._t;
sAnimations.registry.WebsiteSale.include({
	    _changeCountry: function () {
	        if (!$("#country_id").val()) {
	            return;
	        }
	        this._rpc({
	            route: "/shop/country_infos/" + $("#country_id").val(),
	            params: {
	                mode: 'shipping',
	            },
	        }).then(function (data) {
	        	if (data) {
		            // placeholder phone_code
		            //$("input[name='phone']").attr('placeholder', data.phone_code !== 0 ? '+'+ data.phone_code : '');
	        		$(".div_state").show();
	        		$(".div_town").addClass('d-none');
	        		$(".div_district").addClass('d-none');
	        		$(".my_city_id").addClass('d-none');
	        		$(".div_country").after($(".div_state"));
	        		$(".div_zip").removeClass('col-md-6');
	        		$(".div_zip").addClass('col-md-4');
		            // populate states and display
		            var selectStates = $("select[name='state_id']");
		            if (data.states.length){
	            		selectStates.empty();
						var s_option = '';
						var t_emp = '<option value="">State...</option>'
						_.each(data.states,function(value){
							s_option += '<option value=' + value[0] + '>' + value[1] + '</option>'
						})
						selectStates.append(s_option)
		            }else{
		            	var selectStates = $("select[name='state_id']");
			            // dont reload state at first loading (done in qweb)
			            if (selectStates.data('init')===0 || selectStates.find('option').length===1) {
			                if (data.states.length) {
			                    selectStates.html('');
			                    _.each(data.states, function (x) {
			                        var opt = $('<option>').text(x[1])
			                            .attr('value', x[0])
			                            .attr('data-code', x[2]);
			                        selectStates.append(opt);
			                    });
			                    selectStates.parent('div').show();
			                } else {
			                    selectStates.val('').parent('div').hide();
			                }
			                selectStates.data('init', 0);
			            } else {
			                selectStates.data('init', 0);
			            }
		            }
		            // manage fields order / visibility
		            if (data.fields) {
		                if ($.inArray('zip', data.fields) > $.inArray('city', data.fields)){
		                    $(".div_zip").before($(".div_city"));
		                } else {
		                    $(".div_zip").after($(".div_city"));
		                }
		                var all_fields = ["street", "zip", "city", "country_name"]; // "state_code"];
		                _.each(all_fields, function (field) {
		                    $(".checkout_autoformat .div_" + field.split('_')[0]).toggle($.inArray(field, data.fields)>=0);
		                });
		            }
		            ajax.jsonRpc('/hk/country_infos','call',{'country': $("#country_id").val()})
	    	        .then(function (data) {
	    	        	if(data){
	    	        		$("label[for='street']").text("Flat and Floor numbers");
	    	        		$("label[for='street2']").text("Number of building and name of street");
	    	        		$("label[for='street2']").removeClass("label-optional");
	    	        		$(".div_name_building").removeClass('d-none');
	    	        		$(".div_territories").removeClass('d-none');
	    	        	}else{
	    	        		$("label[for='street']").text("Street and Number");
	    	        		$("label[for='street2']").text("Street 2");
	    	        		$("label[for='street2']").addClass("label-optional");
	    	        		$(".div_name_building").addClass('d-none');
	    	        		$(".div_territories").addClass('d-none');
	    	        	}
	    	        });
	        	}else{
	        		$(".div_town").removeClass('d-none');
	        		$(".div_district").removeClass('d-none');
	        		$(".my_city_id").removeClass('d-none');
	        		$(".div_city").hide();
	        		$(".div_state").hide();
	        		$(".div_zip").after($(".div_country"));
	        		$(".div_zip").removeClass('col-md-4');
	        		$(".div_zip").addClass('col-md-6');
	        		
	        		$("label[for='street']").text("Street and Number");
	        		$("label[for='street2']").text("Street 2");
	        		$("label[for='street2']").addClass("label-optional");
	        		$(".div_name_building").addClass('d-none');
	        		$(".div_territories").addClass('d-none');
	        	}
	        });
	    },
	});
});