$(document).ready(function() {

      // 1- Get window width 
      var windowWidth = $(window).width();

      // 2- For all devices under or at 768px, use horizontal orientation
      if(windowWidth <= 767) {
        $('.thumbnails-slides').slick({
            dots: false,
            infinite: false,
            speed: 300,
            slidesToShow: 5,
            vertical: false,
            centerMode: false,
            centerPadding: '40px',
            nextArrow: '<button type="button" class="next ti-angle-down"></button>',
            prevArrow: '<button type="button" class="prev ti-angle-up"></button>'
        });
      } 
      // 3- For all devices over 768px, use vertical orientation
      else {
        $('.thumbnails-slides').slick({
          dots: false,
          loop: true,
          arrows:true,
          infinite: true,
          speed: 300,
          slidesToShow: 5,
          centerMode: false,
          verticalSwiping: true,
          vertical: true,
          nextArrow: '<button type="button" class="next ti-angle-down"></button>',
          prevArrow: '<button type="button" class="prev ti-angle-up"></button>'
        });
      }
      $('.thumbnails-slides').attr('data-slider_look', '1');
});

