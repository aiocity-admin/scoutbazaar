odoo.define('scout_customize.delete_address', function (require) {
"use strict";
var ajax = require('web.ajax')
	$(document).ready(function(){
		var add_model = $('div.justify-content-between')
		$(".deleteaddress").click(function(ev){
	        var deleteaddress = $(this).attr("id");
			ajax.jsonRpc("/my/delete/address", 'call', {'deleteaddress':deleteaddress}).then(function(data){
				if (data){
					window.location.reload();
				}else{
					window.location.reload();
//					var bs_modal1 = '<div class="modal fade" data-backdrop="static" aria-hidden="false" id="my_delete_address" role="dialog" tabindex="-1"><div class="modal-dialog modal-lg" style="width:50%"><div class="modal-content"><div class="modal-header" style ="border-radius:0;background: #e476c3;"><button type="button" class="close" data-dismiss="modal" style="color:black;margin-top: -25px;">×</button><h4 class="modal-title" style="color: white;margin-top:-10px;position:absolute;" id="me_dy-title">WARNING!</h4></div><div class="modal-body alert alert-danger alert-dismissible fade show" style="text-transform: none;margin-bottom:0px;margin-top: -6px;border-radius:0;white-space: pre-line;line-height: normal;text-align:left;">You can not delete this shipping address as it is already used in your past orders!</div></div></div></div>'
//					add_model.append(bs_modal1)
//					$("#my_delete_address").modal("show");
				}
			});
			ev.stopPropagation();
		});
	});
});
