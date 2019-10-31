$(document).ready(function() {
      $('.thumbnails-slides').owlCarousel({
              margin: 10,
              nav:true,
              dots:false,
              responsive: {
                  0: {
                      items: 3,
                  },
                  481: {
                      items: 4,
                  },
                  768: {
                      items: 4,
                  },
                  1024: {
                      items: 5,
                  }
              }
      });
      $('.thumbnails-slides').attr('data-slider_look', '2');
});
