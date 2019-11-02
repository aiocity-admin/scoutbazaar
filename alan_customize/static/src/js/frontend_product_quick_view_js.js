odoo.define('alan_customize.frontend_product_quick_view_js', function(require) {
    'use strict';

    require('web.dom_ready')
    var ajax = require('web.ajax');
    var Widget = require('web.Widget');
    var website = require('web_editor.base');
    var core = require('web.core');
    var qweb = core.qweb;
    var rpc = require('web.rpc');
    var utils = require('web.utils');

    ajax.loadXML('/alan_customize/static/src/xml/quick_view.xml', qweb);

    $(document).off('click', 'a.o_quick_view').on("click", "a.o_quick_view", function(event) {
        var qv_button = $(this);
        qv_button.addClass("disabled");
        var qv_modal = null;
        var attrib_names = new Array();
        var curr_variant_id = 0;
        var QuickView = Widget.extend({
            template: 'quick_view_template',
            events: {
                'click #add_to_cart': 'update_my_cart',
                'click #add_to_wishlist': 'update_my_wishlist',
                'click #add_to_compare': 'update_my_comparelist',
                'click #remove_modal': 'close_modal',
                'change input.js_variant_change,select.js_variant_change': 'update_variant_change'

            },
            init: function() {
                qv_modal = $(this);
                this.prod_id = parseInt(qv_button.attr("data-product_template_id"));
                attrib_names = new Array();
                curr_variant_id = 0;
            },
            start: function() {
                var self = this;
                $.get('/get_prod_quick_view_details', {
                    'prod_id': this.prod_id
                }).then(function(rec) {
                    $("#my_quick_view_modal div.o_product_qv_details").empty().append(rec);
                    attrib_names.length = 0;

                    var temp_names = [];
                    $("#my_quick_view_modal input.js_variant_change,#my_quick_view_modal select.js_variant_change").each(function() {
                        temp_names.push($(this).attr('name'));
                    });
                    temp_names = temp_names.filter(function(value, index, self) {
                        return self.indexOf(value) === index;
                    });
                    attrib_names = temp_names.slice(0);
                    curr_variant_id = $("#my_quick_view_modal input[name='product_id']").val();
                    qv_button.removeClass("disabled");
                    self.$el.modal();
                });
            },
            update_my_cart: function() {
                var $prod_id = $("#my_quick_view_modal input[name='product_id']").val();;
                var $qty_val = $("#my_quick_view_modal div.js_product input[name='add_qty']").val();
                $("#my_quick_view_modal").hide();
                var selected_attribute_value_array = [];
                $.each(attrib_names, function(index, ele) {
                    var attribute_id = parseInt((ele.split("-"))[2]);
                    var attribute_value = parseInt($("input.js_variant_change[name='" + ele + "']:checked").attr("value"));
                    if (!attribute_value)
                        attribute_value = parseInt($("select.js_variant_change[name='" + ele + "'] option:selected").attr("value"));
                    selected_attribute_value_array.push(attribute_value);
                });
                var pi_id = $prod_id
//                Gift Code=======================
                ajax.jsonRpc('/check/order/gift','call',{'p_id': $prod_id}).then(function(sale_order2){
	            	if(sale_order2){
						var bs_modal1 = '<div class="modal fade" data-backdrop="static" aria-hidden="false" id="cart_gift_me" role="dialog" tabindex="-1"><div id="d_me" class="modal-dialog modal-lg" style="width:50%"><div class="modal-content"><div class="modal-header" style ="border-radius:0;background: white;"><button type="button" class="close" data-dismiss="modal" id="view_exit3" style="color:black;margin-top: -25px;">×</button><h4 class="modal-title" style="color: black;font-size: 15px;margin-top:-10px;position:absolute;" id="dy-title">Gift voucher Email</h4></div><div class="modal-body alert alert-danger alert-dismissible fade show" style="height: 200px;text-transform: none;margin-bottom:0px;margin-top: -6px;border-radius:0;white-space: pre-line;line-height: normal;text-align:center;background-color: white;"><b style="font-size: 17px;color: black;font-weight: 600;">Email :</b> <input style="width: 50%;margin-top: 40px;height: 25%;" type="email" class="order_line_email" name="order_line_email" required></input></br><a type="submit" role="button" style="margin-top: 5% !important;color: white;background-color: black;" class="btn btn-primary btn-lg mt8 me_save_as" name="me_save">save</a></div></div></div></div>'
							$(".product_price").append(bs_modal1)
//											$('#my_quick_view_modal').remove();
							$("#cart_gift_me").modal("show");
							$("#view_exit3").click(function(){
								$('.modal-backdrop').removeClass("modal-backdrop fade show");
								$('#my_quick_view_modal').remove();
							});
							$(".me_save_as").mouseover(function(){
								$(".me_save_as").css({'background-color':'#f3847d'})
							});
							$(".me_save_as").mouseout(function(){
								$(".me_save_as").css({'background-color':'black'})
							});
							var in_email = $(".order_line_email").val()
							$('.me_order_line_mail_store').val(in_email)
							$(".me_save_as").on('click', function () {
								var email = $(".order_line_email").val()
								if (email){
									ajax.jsonRpc('/check/order/user','call',{'user_email': email}).then(function(is_user){
										if(is_user){
											$.get('/update_my_cart', {
							                    'prod_id': $prod_id,
							                    'qty_val': $qty_val,
							                    'order_line_email':email,
							                    'attributes': selected_attribute_value_array
							                }).then(function(rec) {
							                    location.reload(true);
							                });
										}else{
											var bs_modal3 = '<div class="modal fade" data-backdrop="static" aria-hidden="false" id="is_user_me" role="dialog" tabindex="-1"><div class="modal-dialog modal-lg" style="width:50%"><div class="modal-content"><div class="modal-header" style ="border-radius:0;background: #e476c3;"><button type="button" class="close" data-dismiss="modal" style="color:black;margin-top: -25px;">×</button><h4 class="modal-title" style="color: white;margin-top:-10px;position:absolute;" id="me_dy-title">WARNING!</h4></div><div class="modal-body alert alert-danger alert-dismissible fade show" style="padding: 81px;text-transform: none;margin-bottom:0px;margin-top: -6px;border-radius:0;white-space: pre-line;line-height: normal;text-align:left;"> Entered "Email" Username does not exists. Please check and re-enter the email. </div></div></div></div>'
											$('.product_price').append(bs_modal3)
											$("#is_user_me").modal("show");
										}
									})
								}
								else{
									$(".order_line_email").css({'border-color':'red'})
									$(".order_line_email").focus();
								}
				            });
	            	}else{
		                $.get('/update_my_cart', {
		                    'prod_id': $prod_id,
		                    'qty_val': $qty_val,
		                    'attributes': selected_attribute_value_array
		                }).then(function(rec) {
		                    location.reload(true);
		                });
	            	}
                })
                
                
                
//                $.get('/update_my_cart', {
//                    'prod_id': $prod_id,
//                    'qty_val': $qty_val,
//                    'attributes': selected_attribute_value_array
//                }).then(function(rec) {
//                    location.reload(true);
//                });
            },
            update_my_wishlist: function() {
                var $prod_id = $("#my_quick_view_modal input[name='product_id']").val();
                $("#myModal").hide();
                $.get('/update_my_wishlist', {
                    'prod_id': $prod_id
                }).then(function(rec) {
                    location.reload(true);
                });
            },
            update_my_comparelist: function() {
                qv_button.parent().find(".o_add_compare").each(function() {
                    var curr_val = $(this).attr("data-product-product-id");
                    var $prod_id = curr_variant_id;
                    $(this).data("product-product-id", parseInt($prod_id));
                    $(this).trigger("click", function() {
                        $(this).data("product-product-id", curr_val);
                    });
                });
            },
            update_variant_change: function(e) {
                if (attrib_names.length > 0) {
                    var $parent = $(e.target).parent();
                    if ($parent.hasClass("css_attribute_color")) {
                        $parent.addClass("active");
                        $parent.parents("ul").find(".css_attribute_color").not($parent).removeClass("active");
                    }
                    var selected_attribute_value_array = [];
                    $.each(attrib_names, function(index, ele) {
                        var attribute_id = parseInt((ele.split("-"))[2]);
                        var attribute_value = parseInt($("input.js_variant_change[name='" + ele + "']:checked").attr("value"));
                        if (!attribute_value)
                            attribute_value = parseInt($("select.js_variant_change[name='" + ele + "'] option:selected").attr("value"));
                        selected_attribute_value_array.push(attribute_value);
                    });
                    ajax.jsonRpc("/get_qv_prod_variant", 'call', {
                        'prod_template_id': parseInt((attrib_names[0].split("-"))[1]),
                        'attribute_values_array': selected_attribute_value_array,
                    }).then(function(variant_data) {
                        curr_variant_id = variant_data.product_product_id;
                    });
                }
            },
            close_modal: function(e) {
                $('#my_quick_view_modal').remove();
            }
        });

        website.ready().done(function() {
            $("#my_quick_view_modal").remove();
            new QuickView().appendTo('.oe_website_sale');
        });
    });
});