$(document).ready(function () {
	odoo.define('scout_baazar.website_side', function (require) {
    "use strict";
    var ajax = require('web.ajax');
	var aaa=$('#school_id')
	$(aaa).select2({placeholder: 'Select an option'});
	});
});  