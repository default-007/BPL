jQuery(document).ready(function ($) {
    "use strict";

    // Preloader
    // ------------------------------------------------------
    $(window).on('load', function () {
        anime.timeline({
                targets: '.preloader',
                easing: 'easeOutExpo',
            })
            .add({
                height: ['100vh', '0vh'],
                duration: 700,
                delay: 2000,
            })
            .add({
                offset: '-=400',
                complete: function (anim) {
                    document.querySelector('.preloader').remove();
                }
            })
            .add({
                offset: '-=1300',
                targets: '#site-wrapper',
                top: 0,
                duration: 700,
            })

        anime.timeline({
                easing: 'easeOutExpo',
            })
            .add({
                targets: '.preloader .txt',
                delay: 100,
                opacity: 1,
                duration: 700,
                translateY: ["30px", "0px"],
            })
            .add({
                targets: '.preloader .progress',
                offset: '-=400',
                opacity: 1,
                duration: 700,
            })
            .add({
                targets: ".preloader .progress .bar-loading",
                offset: '-=400',
                duration: 2000,
                width: ["0", "100%"],
            })
            .add({
                targets: '.preloader .loading',
                offset: '-=900',
                opacity: 0,
                duration: 1000,
                translateY: ["0", "-100px"],
            })
    });

    // Main Sliders
    // ------------------------------------------------------

    $(".owl-carousel").each(function (index) {
        var items = $(this).data('items'),
            autoplay = $(this).data('autoplay'),
            margin = $(this).data('margin'),
            loop = $(this).data('loop'),
            center = $(this).data('center'),
            dots = $(this).data('dots'),
            nav = $(this).data('nav');
        $(this).owlCarousel({
            items: items,
            autoplay: autoplay,
            margin: margin,
            autoplayHoverPause: true,
            smartSpeed: 450,
            loop: loop,
            center: center,
            dots: dots,
            dotsEach: true,
            nav: nav,
            responsive: {
                0: {
                    items: 1
                },
                640: {
                    items: 1
                },
                960: {
                    items: 2
                },
                1200: {
                    items: 3
                },
                1600: {
                    items: items
                }
            }
        });
    });

    // Contact Form Validate JS
    // ------------------------------------------------------

    if ($('.pr__contact').length) {
        $('.pr__contact').validate({ // Initialize the plugin
            rules: {
                name: {
                    required: true
                },
                email: {
                    required: true,
                    email: true
                },
                message: {
                    required: true
                }
            },
            submitHandler: function (form) {
                var $form = $(form);
                var $status = $form.find('.pr__contact__status');
                var $button = $form.find('[type="submit"]');

                function showStatus(ok, text) {
                    $status
                        .removeClass('uk-alert-success uk-alert-danger')
                        .addClass('uk-alert ' + (ok ? 'uk-alert-success' : 'uk-alert-danger'))
                        .text(text);
                }

                $button.prop('disabled', true);
                $.ajax({
                    url: $form.attr('action'),
                    type: 'POST',
                    data: $form.serialize(),
                    dataType: 'json'
                }).done(function (response) {
                    showStatus(true, response.message);
                    $form.find('input[type="text"], input[type="email"], textarea').val('');
                }).fail(function (xhr) {
                    var response = xhr.responseJSON || {};
                    var text = response.message || 'Sorry, something went wrong. Please email us at info@bakpagelabs.com.';
                    $.each(response.errors || {}, function (field, errors) {
                        text += ' ' + errors.join(' ');
                    });
                    showStatus(false, text);
                }).always(function () {
                    $button.prop('disabled', false);
                });
                return false;
            }
        });
    }

});