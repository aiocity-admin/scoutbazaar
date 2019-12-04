odoo.define('website_scout_baazar.product_attachment', function (require) {
    'use strict';
    var ajax = require('web.ajax')

    $(document).ready(function(){
    	
    	var product_id = $('#product_details .js_product.js_main_product input.product_id').val()

    	if (product_id){
    		ajax.jsonRpc('/get/product_document','call',{'product_id': product_id}).then(function(links){
    			if(links){

    				var document_tab = $('div#document .row.document_row')

    				document_tab.empty()
    				_.each(links,function(key,value){
			           var card_tag = '<div class="col-lg-2 document_attachments card text-white" style="background-color:#1998a7;margin-right: 10px;margin-bottom:3px;height:150px;">'
			           card_tag += '<span class="card-body value_attachment" style="color: #fdfdfd;font-size: 12px;">' + value + '</span>';
			           card_tag += '<a class="cards download_attach_file" style="color: #f9bc46;" href="' + key + '"><i class="fa fa-download fa_download" style="font-size: 25px;" aria-label="Download" role="img"> </i>' + '</a>';
			           card_tag += '</div>';
			           document_tab.append(card_tag);

    				})
    			}
    		})
    	}
    })
});