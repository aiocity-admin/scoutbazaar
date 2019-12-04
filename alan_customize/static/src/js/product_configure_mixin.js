odoo.define('alan_customize.ProductConfiguratorMixin', function (require) {
    'use strict';
    var sAnimations = require('website.content.snippets.animation');
    var core = require('web.core');
    var QWeb = core.qweb;
    var ajax = require('web.ajax');
    var ProductConfiguratorMixin = require('sale.ProductConfiguratorMixin');
    
    sAnimations.registry.WebsiteSale.include({
        _onChangeCombination: function (){
            this._super.apply(this, arguments);
            this._onChangeCombinationImage.apply(this, arguments);
        },
        _onChangeCombinationImage: function (ev, $parent, combination) {
            var isMainProduct = combination.product_id &&
                ($parent.is('.js_main_product') || $parent.is('.main_product')) &&
                combination.product_id === parseInt($parent.find('.product_id').val());

            if (!this.isWebsite || !isMainProduct){
                return;
            }

            if(combination.product_id){
                var $t_slides = $("#pro_detail_zoom");
                ajax.jsonRpc("/variant_change_images", 'call', {
                    'product_id': combination.product_id
                }).then(function (data){
                    if(data.value_ret === 1){
                        var $prod_img_box = $("#product_detail .product-img-box");
                        if($t_slides.attr("data-slider_look") === '1'){
                            $t_slides.slick('unslick');
                            if(data.main_img.trim())
                                $prod_img_box.find(".img-gallery_popup span.main_image").replaceWith(data.main_img.trim());
                            $t_slides.removeClass().addClass("thumbnails-slides");
                            if(data.sub_img.trim())
                                $t_slides.empty().append(data.sub_img.trim());
                            $.getScript("/alan_customize/static/src/scss/options/product-details/option-1.js");
                            if(data.opt_zoom === 1)
                                $.getScript("/alan_customize/static/src/js/zoom.js");
                            if(data.opt_gallery === 1)
                                $.getScript("/alan_customize/static/src/js/product_image_gallery_js.js");
                            $("img.sub-images").click(function(ev) {
                                ev.preventDefault();
                                ev.stopPropagation();
                                $('.product_detail_img').attr('src', this.src);
                                $('.product_detail_img').parent().parent().attr('src', this.src);
                            });
                        }
                        else if($t_slides.attr("data-slider_look") === '2'){
                            $t_slides.trigger('destroy.owl.carousel').removeClass('owl-loaded');
                            if(data.main_img.trim())
                                $prod_img_box.find(".img-gallery_popup span.main_image").replaceWith(data.main_img.trim());
                            $t_slides.removeClass().addClass("thumbnails-slides owl-carousel");
                            if(data.sub_img.trim())
                                $t_slides.empty().append(data.sub_img.trim());
                            $.getScript("/alan_customize/static/src/scss/options/product-details/option-2.js");
                            if(data.opt_zoom === 1)
                                $.getScript("/alan_customize/static/src/js/zoom.js");
                            if(data.opt_gallery === 1)
                                $.getScript("/alan_customize/static/src/js/product_image_gallery_js.js");
                            $("img.sub-images").click(function(ev) {
                                ev.preventDefault();
                                ev.stopPropagation();
                                $('.product_detail_img').attr('src', this.src);
                                $('.product_detail_img').parent().parent().attr('src', this.src);
                            });
                        }
                        
                    }
                });
            }
        },
    });

    sAnimations.registry.ProductWishlist.include({
        _updateWishlistView: function () {
            if (this.wishlistProductIDs.length > 0) {
                $('#my_wish').show();
                $('.my_wish_quantity').text(this.wishlistProductIDs.length);
            }
        },
    });  

    return sAnimations.registry.WebsiteSale;
});
