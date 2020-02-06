odoo.define('sh_shop_qty.website_sale', function (require) {
'use strict';

var sAnimations = require('website.content.snippets.animation');


sAnimations.registry.WebsiteSale.include({
    events: ({

        'change input[name="add_qty"]': '_onChangeAddQuantityCustom',   
    
    }),
    
    
	//--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {MouseEvent} ev
     */
    _onClickAddCartJSON: function (ev){
        ev.preventDefault();
        var $link = $(ev.currentTarget);

        var $input = $link.closest('.input-group').find("input");
        var min = parseFloat($input.data("min") || 0);
        var setqty = parseFloat($input.data("setqty") || 1);
        var max = parseFloat($input.data("max") || Infinity);
        var quantity = ($link.has(".fa-minus").length ? -1 : 1) + parseFloat($input.val() || 0, 10);
        var newQty = quantity > min ? (quantity < max ? quantity : max) : min;
        $input.val(newQty).trigger('change');
        return false;  	
  
    },    
    
    
    _onChangeAddQuantityCustom:function(ev){
        ev.preventDefault();    	
    	var data = $('input[name="add_qty"]').val();
    	var default_value = $('input[name="add_qty"]').data('setqty');
    	if(parseInt(data) < parseInt(default_value)){
    		var set_data = default_value;
    		document.getElementById("qty_id").value = set_data;
    	}
    	
    
        return false;      	
    },   
    
 
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private override
     */
    _changeCartQuantity: function ($input, value, $dom_optional, line_id, productIDs) {
        this._super.apply(this, arguments);    	
        
    	var data = value;
    	var default_value = $input.data('setqty');
    	if(value != 0){
    	if(parseInt(data) < parseInt(default_value)){
    		var set_data = default_value;
    		//document.getElementById("qty_id").value = set_data;
    		$input.val(set_data);
    	}
    	
    	}
           
    	
    },          
    
});

});
