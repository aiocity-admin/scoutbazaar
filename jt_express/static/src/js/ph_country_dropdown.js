odoo.define('jt_express.ph_country', function (require) {
'use strict';

var utils = require('web.utils');
var ProductConfiguratorMixin = require('sale.ProductConfiguratorMixin');
var core = require('web.core');
var config = require('web.config');
var sAnimations = require('website.content.snippets.animation');
require("website.content.zoomodoo");

var CountryOnchage = require('website_sale.website_sale');
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
//	        		$("input[name='phone']").attr('placeholder', data.phone_code !== 0 ? '+'+ data.phone_code : '');
	        		$(".div_state").show();
	        		$(".div_town").addClass('d-none');
	        		$(".div_district").addClass('d-none');
	        		$(".my_city_id").addClass('d-none');
	        		$(".div_country").after($(".div_state"));
	        		$(".div_zip").removeClass('col-md-6');
	        		$(".div_zip").addClass('col-md-4');
		            // populate states and display
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
	        	}else{
	        		$(".div_town").removeClass('d-none');
	        		$(".div_district").removeClass('d-none');
	        		$(".my_city_id").removeClass('d-none');
	        		$(".div_city").hide();
	        		$(".div_state").hide();
	        		$(".div_zip").after($(".div_country"));
	        		$(".div_zip").removeClass('col-md-4');
	        		$(".div_zip").addClass('col-md-6');
	        	}
	        });
	    },
	});

	$(document).ready(function(){
	    var int_phone = $("input[name='phone']");
	    if (int_phone){
			int_phone.change(function(){
				var val = int_phone.val();
				if (val){
					if (val.length < 10) {
						int_phone.val('')
						int_phone.attr('placeholder', 'Please Enter Phone number more than 10 character!');
					}
				}
			})
	    }
	    
	    var city = $("select[name='city_id']");
	    var district = $("select[name='district_id']");
	    var town = $("select[name='town_id']");
	    var div_model = $('div#wrap');
	    var city_lg = $(city).children("option:selected").val()
	    var district_lg = $(district).children("option:selected").val()
	    if (district_lg){
	    }else{
	    	town.empty();
	    }
	    if (city_lg){
	    }else{
	    	district.empty();
	    }
	    
	    if (town){
		    town.change(function(){
				var d_l = $(district).children("option:selected").val();
				if (d_l){
				}else{
					town.empty();
					var bs_modal1 = '<div class="modal fade" data-backdrop="static" aria-hidden="false" id="select_town" role="dialog" tabindex="-1"><div class="modal-dialog modal-lg" style="width:50%"><div class="modal-content"><div class="modal-header" style ="border-radius:0;background: #e476c3;"><button type="button" class="close" data-dismiss="modal" style="color:black;margin-top: -25px;">×</button><h4 class="modal-title" style="color: white;margin-top:-10px;position:absolute;" id="me_dy-title">WARNING!</h4></div><div class="modal-body alert alert-danger alert-dismissible fade show" style="text-transform: none;margin-bottom:0px;margin-top: -6px;border-radius:0;white-space: pre-line;line-height: normal;text-align:left;">Please Select City / Municipality !</div></div></div></div>'
					div_model.append(bs_modal1)
					$("#select_town").modal("show");
				}
			})
	    }
	    
	    if (district){
	    	district.change(function(){
				var district_id = $(this).children("option:selected").val();
				var c_l = $(city).children("option:selected").val();
				if (c_l){
				}else{
					district.empty();
					var bs_modal2 = '<div class="modal fade" data-backdrop="static" aria-hidden="false" id="select_dictrict" role="dialog" tabindex="-1"><div class="modal-dialog modal-lg" style="width:50%"><div class="modal-content"><div class="modal-header" style ="border-radius:0;background: #e476c3;"><button type="button" class="close" data-dismiss="modal" style="color:black;margin-top: -25px;">×</button><h4 class="modal-title" style="color: white;margin-top:-10px;position:absolute;" id="me_dy-title">WARNING!</h4></div><div class="modal-body alert alert-danger alert-dismissible fade show" style="text-transform: none;margin-bottom:0px;margin-top: -6px;border-radius:0;white-space: pre-line;line-height: normal;text-align:left;">Please Select Province !</div></div></div></div>'
					div_model.append(bs_modal2)
					$("#select_dictrict").modal("show");
				}
				
				if (district_id){
					ajax.jsonRpc('/filter/ph_servicable_area/district','call',{'district_id':district_id}).then(function (data) {
						if (data){
							town.empty();
							var town_option = '';
							var t_emp = '<option value="">Barangay...</option>'
							_.each(data,function(value){
								town_option += '<option value=' + value[0] + '>' + value[1] + '</option>'
							})
							town.append(t_emp + town_option)
						}else{
							town.empty();
						}
					})
				}
			})
	    }
	    
	    if (city){
		   city.change(function(){
				var city_id = $(this).children("option:selected").val();
				if (city_id){
					ajax.jsonRpc('/filter/ph_servicable_area','call',{'city_id':city_id}).then(function (data) {
						if (data){
							district.empty();
							town.empty();
							var district_option = '';
							var town_option = '';
							var d_emp = '<option value="">City / Municipality...</option>'
							_.each(data[0],function(value){
								district_option += '<option value=' + value[0] + '>' + value[1] + '</option>'
							})
							district.append(d_emp + district_option)
							
							var t_emp = '<option value="">Barangay...</option>'
							_.each(data[1],function(value){
								town_option += '<option value=' + value[0] + '>' + value[1] + '</option>'
							})
							town.append(t_emp + town_option)
						}else{
							town.empty();
							district.empty();
						}
					})
				}
			})
	   }
	});
	
});