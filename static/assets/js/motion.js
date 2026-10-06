/* BakPage Labs — motion layer (Lenis smooth scroll + GSAP reveals)
   Loaded after redesign.js. Requires window.Lenis and window.gsap (CDN).
   Fully skipped under prefers-reduced-motion: reduce — content is visible
   and unanimated immediately in that case. */
(function () {
	"use strict";

	var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

	function $$(selector, scope) {
		return Array.prototype.slice.call((scope || document).querySelectorAll(selector));
	}

	function initSmoothScroll() {
		if (reduceMotion || typeof window.Lenis === "undefined" || typeof window.gsap === "undefined") {
			return null;
		}
		var lenis = new window.Lenis();
		var onScroll = window.ScrollTrigger ? window.ScrollTrigger.update : function () {};
		lenis.on("scroll", onScroll);
		window.gsap.ticker.add(function (time) {
			lenis.raf(time * 1000);
		});
		window.gsap.ticker.lagSmoothing(0);
		return lenis;
	}

	function initReveals() {
		if (reduceMotion || typeof window.gsap === "undefined" || typeof window.ScrollTrigger === "undefined") {
			return;
		}
		window.gsap.registerPlugin(window.ScrollTrigger);

		$$(".bp-section, .bp-offset, .bp-work-card, .bp-tile, .bp-studio-card, .bp-testimonial").forEach(function (el) {
			window.gsap.from(el, {
				opacity: 0,
				y: 24,
				duration: 0.6,
				ease: "power2.out",
				scrollTrigger: {
					trigger: el,
					start: "top 85%",
					once: true
				}
			});
		});
	}

	function initStatCounters() {
		if (reduceMotion || typeof window.gsap === "undefined") {
			return;
		}
		$$("[data-bp-count]").forEach(function (el) {
			var target = parseFloat(el.getAttribute("data-bp-count"));
			if (isNaN(target)) return;
			var counter = { value: 0 };
			var vars = {
				value: target,
				duration: 1.4,
				ease: "power1.out",
				onUpdate: function () {
					el.textContent = Math.round(counter.value);
				}
			};
			if (window.ScrollTrigger) {
				vars.scrollTrigger = { trigger: el, start: "top 90%", once: true };
			}
			window.gsap.to(counter, vars);
		});
	}

	function init() {
		initSmoothScroll();
		initReveals();
		initStatCounters();
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", init);
	} else {
		init();
	}
})();
