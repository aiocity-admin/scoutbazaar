odoo.define('alan_customize.product_image_gallery_js', function(require){
    'use strict';

    var ajax = require('web.ajax');
    var core = require('web.core');
    var qweb = core.qweb;

    $(document).ready(function(){
        var $img_slider = $("section#product_detail .product-img-box .thumbnails-slides");
        $("section#product_detail .product-img-box .img-gallery_popup").bind('click', function(e){
            $("#image_gallery_slider").remove();

            var curr_slide_url = $(this).find("img.product_detail_img").prop('src');
            $.get('/get_product_img_gallery', {
                'product_id': $("#product_details .js_main_product input[name='product_id']").val()
            }).then(function(data){
                if(data.trim()){
                    $("#image_gallery_slider").remove();
                    $('.modal-backdrop').remove();
                    $("body").append(data.trim());
                    $("body > #image_gallery_slider.modal").modal();
                    $("body > #image_gallery_slider.modal").on("shown.bs.modal", function(){
                        $(this).find(".gallery_img.owl-carousel").owlCarousel({
                            items: 1,
                            margin: 0,
                            navigation: true,
                            pagination: true,
                            // loop: true,
                        });
                        var goto_index = 0;
                        $(this).find(".gallery_img.owl-carousel .item img.sub-images").each(function(index, obj){
                            if($(this).prop('src') === curr_slide_url)
                                goto_index = index;
                        });
                        $(this).find(".gallery_img.owl-carousel").trigger('to.owl.carousel', goto_index);
                    });

                    $("body > #image_gallery_slider.modal").on('hidden.bs.modal', function () {
                        $(this).remove();
                    });
                }
            });
        });
    });
});
