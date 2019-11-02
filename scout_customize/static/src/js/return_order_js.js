var ajax;
var rpc;
odoo.define('scout_customize.return_order_js', function (require) {
'use strict';
	ajax = require('web.ajax');
	rpc = require('web.rpc');
});

function myFunction_prodcut()
{
	var selectedreturproduct = $(".cut_p").val();
	if(selectedreturproduct){
		$(".than_less").addClass('d-none');
		$(".my_button").removeClass('d-none');
		$(".than_zero").addClass('d-none');
		var doxInputID = $('#input_return_product')
		doxInputID.val(selectedreturproduct)
		ajax.jsonRpc('/check/qty','call',{'line_id': selectedreturproduct}).then(function(line_qty){
			if(line_qty > 0){
				$(".than_less").addClass('d-none');
				$('.return_quantity').val(Math.max(line_qty));
				$(".than_zero").addClass('d-none');
				$(".my_button").removeClass('d-none');
			}else{
	            $('.return_quantity').val('');
	            $(".my_button").addClass('d-none');
	            $(".than_zero").removeClass('d-none');
//	            alert("product line qty is 0")
	            return false
			}
		})
	}else{
		$(".my_button").addClass('d-none');
		$('.return_quantity').val('');
		$(".than_zero").removeClass('d-none');
//		alert("You have selected the Product");
	}
}

function myFunction_prodcut_qty()
{	
	line_id = $(".cut_p").val();
	if(line_id){
		ajax.jsonRpc('/check/qty','call',{'line_id': line_id}).then(function(line_qty){
			if(line_qty > 0){
				$(".my_button").removeClass('d-none');
				$(".than_zero").addClass('d-none');
				a = $('.return_quantity').val();
		        if (a>=1 && a<=line_qty) {
		        	$(".than_less").addClass('d-none');
		        	$(".my_button").removeClass('d-none');
		            return true
		        }else{
		        	$(".my_button").addClass('d-none');
		        	$(".than_less").removeClass('d-none');
//		            $('.return_quantity').val(line_qty);
//		            alert("Must be between 1 and "+line_qty)
		            return false
		        }
			}else{
				$(".my_button").addClass('d-none');
	            $('.return_quantity').val('');
	            $(".than_zero").removeClass('d-none');
//	            alert("product line qty is 0")
	            return false
			}
		})
	}else{
		$('.return_quantity').val(0);
	}
}