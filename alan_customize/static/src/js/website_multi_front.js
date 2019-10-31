odoo.define('alan_customize.front_js_multi', function(require) {
    'use strict';

    var sAnimation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');

    function initialize_owl(el) {
        el.owlCarousel({
            items: 4,
            margin: 25,
            navigation: true,
            pagination: false,
            responsive: {
                0: {
                    items: 1,
                },
                481: {
                    items: 2,
                },
                768: {
                    items: 3,
                },
                1024: {
                    items: 4,
                }
            }

        });
    }

    function initialize_owl_1(el) {
        el.owlCarousel({
            items: 4,
            margin: 25,
            navigation: true,
            pagination: false,
            responsive: {
                0: {
                    items: 1,
                },
                481: {
                    items: 2,
                },
                768: {
                    items: 2,
                },
                1024: {
                    items: 4,
                }
            }
        });
    }

    function initialize_owl_multi(el) {
        el.owlCarousel({
            items: 4,
            margin: 25,
            navigation: true,
            pagination: false,
            responsive: {
                0: {
                    items: 1,
                },
                481: {
                    items: 2,
                },
                768: {
                    items: 3,
                },
                1024: {
                    items: 4,
                }
            }

        });
    }

    function destory_owl(el) {
        if (el && el.data('owlCarousel')) {
            el.data('owlCarousel').destroy();
            el.find('.owl-stage-outer').children().unwrap();
            el.removeData();
        }
    }

    sAnimation.registry.s_product_multi_with_header = sAnimation.Class.extend({
        selector: ".js_multi_collection",
        start: function(editMode) {
            var self = this;
            if (self.editableMode) {
                self.$target.empty().append('<div class="container"><div class="product_slide" contentEditable="false"><div class="col-md-12"><div class="seaction-head"<h1>Multitab Product with Header</h1></div></div></div></div>');
            }
            if (!self.editableMode) {
                var list_id = self.$target.attr('data-list-id') || false;
                $.get("/shop/get_multi_tab_content", {
                    'collection_id': list_id
                }).then(function(data) {
                    if (data) {
                        self.$target.empty().append(data);
                        $(".js_multi_collection").removeClass('hidden');
                        $('a[data-toggle="tab"]').on('shown.bs.tab', function() {
                            initialize_owl($(".multi_tab_slider .tab-content .active .multi_slider"));
                        }).on('hide.bs.tab', function() {
                            destory_owl($(".multi_tab_slider .tab-content .active .multi_slider"));
                        });
                        initialize_owl($(".multi_tab_slider .tab-content .active .multi_slider"));
                    }
                });
            }
        },
    });

    sAnimation.registry.s_product_multi_snippet = sAnimation.Class.extend({
        selector: ".multi_tab_product_snippet",
        start: function(editMode) {
            var self = this;
            self.$target.empty();
            if (self.editableMode) {
                self.$target.empty().append('<div class="container"><div class="product_slide" contentEditable="false"><div class="col-md-12"><div class="seaction-head"<h1>Multitab Product with Header</h1></div></div></div></div>');
            }
            if (!self.editableMode) {
                var list_id = self.$target.attr('data-list-id') || false;
                $.get("/shop/multi_tab_product_snippet", {
                    'collection_id': list_id
                }).then(function(data) {
                    if (data) {
                        self.$target.empty().append(data);
                        $(".multi_tab_product_snippet").removeClass('hidden');
                    }
                });
            }
        },
    });

    $(document).ready(function() {
        $('.multi_tab_slider li a[data-toggle="tab"]').on('shown.bs.tab', function() {
            $(".multi_slider").owlCarousel({
                items: 4,
                margin: 25,
                navigation: true,
                pagination: false,
                responsive: {
                    0: {
                        items: 1,
                    },
                    481: {
                        items: 2,
                    },
                    768: {
                        items: 3,
                    },
                    1024: {
                        items: 4,
                    }
                }
            });
        });
    });

    sAnimation.registry.s_brand_multi_with_header = sAnimation.Class.extend({
        selector: ".js_brand_multi_collection",
        start: function(editMode) {
            var self = this;
            if (self.editableMode) {
                self.$target.empty().append('<div class="container"><div class="product_slide" contentEditable="false"><div class="col-md-12"><div class="seaction-head"<div class="h1">Brand Collection Slider</div></div></div></div></div>');
            }

            if (!self.editableMode) {
                var list_id = self.$target.attr('data-list-id') || false;
                ajax.jsonRpc("/shop/get_brand_multi_tab_content", 'call', {
                    'collection_id': list_id
                }).then(function(data) {
                    if (data) {
                        var slider = data.slider
                        var auto_slider_value = data.auto_slider_value
                        var item_count = data.item_count
                        var slider_timing = data.slider_timing
                        self.$target.empty().append(slider);
                        $(".js_brand_multi_collection").removeClass('hidden');
                        $.getScript("/alan_customize/static/src/js/owl.carousel.min.js");
                        self.$target.find("#as_our_brand").owlCarousel({
                            items: parseInt(item_count) || 4,
                            loop: true,
                            margin: 10,
                            autoplay: auto_slider_value || false,
                            autoplaySpeed: parseInt(slider_timing) || 5000,
                            autoplayHoverPause: true,
                            navigation: true,
                            pagination: false,
                            responsive: {
                                0: {
                                    items: 2,
                                },
                                481: {
                                    items: 3,
                                },
                                768: {
                                    items: 4,
                                },
                                1024: {
                                    items: parseInt(item_count) || 4,
                                }
                            }
                        });
                    }
                });
            }
        },
    });
});