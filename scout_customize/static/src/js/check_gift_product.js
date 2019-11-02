 odoo.define('scout_customize.check_is_gift_product', function (require) {
"use strict";

var ajax = require('web.ajax')
var check_warehouse  = require("website_sale_options.website_sale")
	check_warehouse.include({
	    _onClickAdd: function (ev) {
				var self = this
					var p_id = $(ev.currentTarget).parent().find("input").val()
					if(p_id){
						ajax.jsonRpc('/check/gift','call',{'p_id': p_id}).then(function(sale_order2){
							if(sale_order2){
								var bs_modal1 = '<div class="modal fade" data-backdrop="static" aria-hidden="false" id="cart_gift_me" role="dialog" tabindex="-1"><div class="modal-dialog modal-lg" style="width:50%"><div class="modal-content"><div class="modal-header" style ="border-radius:0;background: white;"><button type="button" class="close" data-dismiss="modal" style="color:black;margin-top: -25px;">×</button><h4 class="modal-title" style="color: black;font-size: 15px;margin-top:-10px;position:absolute;" id="dy-title">Gift voucher Email</h4></div><div class="modal-body alert alert-danger alert-dismissible fade show" style="height: 200px;text-transform: none;margin-bottom:0px;margin-top: -6px;border-radius:0;white-space: pre-line;line-height: normal;text-align:center;background-color: white;"><b style="font-size: 17px;color: black;font-weight: 600;">Email :</b> <input style="width: 50%;margin-top: 40px;height: 25%;" type="email" class="order_line_email" name="order_line_email" required></input></br><a type="submit" role="button" style="margin-top: 5% !important;color: white;background-color: black;" class="btn btn-primary btn-lg mt8 me_save_as" name="me_save">save</a></div></div></div></div>'
									$(".product_price").append(bs_modal1)
									$("#cart_gift_me").modal("show");

									$(".me_save_as").mouseover(function(){
										$(".me_save_as").css({'background-color':'#f3847d'})
									});
									$(".me_save_as").mouseout(function(){
										$(".me_save_as").css({'background-color':'black'})
									});
									var in_email = $(".order_line_email").val()
									$(".me_save_as").on('click', function () {
										var email = $(".order_line_email").val()
										if (email){
											ajax.jsonRpc('/check/user','call',{'user_email': email}).then(function(is_user){
												if(is_user){
													return self._handleAdd($(ev.currentTarget).closest('form'));
												}else{
													var bs_modal3 = '<div class="modal fade" data-backdrop="static" aria-hidden="false" id="is_user_me" role="dialog" tabindex="-1" style="padding-right: 15px;"><div class="modal-dialog modal-lg" style="width:50%"><div class="modal-content"><div class="modal-header" style ="border-radius:0;background: #e476c3;"><button type="button" class="close" data-dismiss="modal" style="color:black;margin-top: -25px;">×</button><h4 class="modal-title" style="color: white;margin-top:-10px;position:absolute;" id="me_dy-title">WARNING!</h4></div><div class="modal-body alert alert-danger alert-dismissible fade show" style="padding: 81px;text-transform: none;margin-bottom:0px;margin-top: -6px;border-radius:0;white-space: pre-line;line-height: normal;text-align:left;"> Entered "Email" Username does not exists. Please check and re-enter the email. </div></div></div></div>'
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
								return self._handleAdd($(ev.currentTarget).closest('form'));
							}
						})
					}else{
						return self._handleAdd($(ev.currentTarget).closest('form'));
					}
	    },
	});
});
   