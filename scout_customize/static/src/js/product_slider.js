odoo.define('scout_customize.product_slider_image', function (require) {
"use strict";   
var utils = require('web.utils');
var ProductConfiguratorMixin = require('sale.ProductConfiguratorMixin');
var core = require('web.core');
var config = require('web.config');

var sAnimations = require('website.content.snippets.animation');
require("website.content.zoomodoo");
	sAnimations.registry.WebsiteSale.include({
	

		_updateProductImage: function ($productContainer, productId, productTemplateId, new_carousel) {
	        var $img;
	        var product = $productContainer.find('.owl-stage');
	        
	        if (product[0].children.length > 4){
	              $('.thumbnails-slides').slick({
	              dots: false,
	              vertical: true,
	              infinite: true,
	              speed: 300,
	              slidesToShow: 4,
	              centerMode: false,
	              verticalSwiping: true,
	              nextArrow: '<button type="button" class="next ti-angle-down"></button>',
	              prevArrow: '<button type="button" class="prev ti-angle-up"></button>'
	            });
	        }
	        else{
	            return false
	        }

	        var $carousel = $productContainer.find('#o-carousel-product');

	        if (new_carousel) {
	            // When using the web editor, don't reload this or the images won't
	            // be able to be edited depending on if this is done loading before
	            // or after the editor is ready.
	            if (window.location.search.indexOf('enable_editor') === -1) {
	                var $new_carousel = $(new_carousel);
	                $carousel.after($new_carousel);
	                $carousel.remove();
	                $carousel = $new_carousel;
	                $carousel.carousel(0);
	                this._startZoom();
	                // fix issue with carousel height
	                this.trigger_up('animation_start_demand', {$target: $carousel});
	            }
	        }
	        else { // compatibility 12.0
	            var model = productId ? 'product.product' : 'product.template';
	            var modelId = productId || productTemplateId;
	            var imageSrc = '/web/image/{0}/{1}/image'
	                .replace("{0}", model)
	                .replace("{1}", modelId);

	            $img = $productContainer.find('img.js_variant_img');
	            $img.attr("src", imageSrc);
	            $img.parent().attr('data-oe-model', model).attr('data-oe-id', modelId)
	                .data('oe-model', model).data('oe-id', modelId);

	            var $thumbnail = $productContainer.find('img.js_variant_img_small');
	            if ($thumbnail.length !== 0) { // if only one, thumbnails are not displayed
	                $thumbnail.attr("src", "/web/image/{0}/{1}/image/90x90"
	                    .replace('{0}', model)
	                    .replace('{1}', modelId));
	                $('.carousel').carousel(0);
	            }

	            // reset zooming constructs
	            $img.filter('[data-zoom-image]').attr('data-zoom-image', $img.attr('src'));
	            if ($img.data('zoomOdoo') !== undefined) {
	                $img.data('zoomOdoo').isReady = false;
	            }
	        }

	        $carousel.toggleClass('css_not_available', !this.isSelectedVariantAllowed);
	    },

	});
});