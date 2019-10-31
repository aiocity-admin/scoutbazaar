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
                $.get('/update_my_cart', {
                    'prod_id': $prod_id,
                    'qty_val': $qty_val,
                    'attributes': selected_attribute_value_array
                }).then(function(rec) {
                    location.reload(true);
                });
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
