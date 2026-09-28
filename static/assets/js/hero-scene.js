/* BakPage Labs — hero background scene (Three.js)
   Subtle drifting particle field confined to [data-bp-hero-scene] hero
   backgrounds. Lazy-instantiated once the hero enters the viewport, paused
   off-screen / when the tab is hidden, and skipped entirely under
   prefers-reduced-motion or when WebGL / a reasonable GPU isn't available —
   in every skipped case the existing static hero image + gradient is the
   fallback, so there is no visual regression. */
(function () {
	"use strict";

	var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
	var lowPower = typeof navigator.hardwareConcurrency === "number" && navigator.hardwareConcurrency <= 2;

	function supportsWebGL() {
		try {
			var canvas = document.createElement("canvas");
			return !!(window.WebGLRenderingContext && canvas.getContext("webgl"));
		} catch (e) {
			return false;
		}
	}

	function buildScene(canvas) {
		var THREE = window.THREE;
		var renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
		renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));

		var scene = new THREE.Scene();
		var camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
		camera.position.z = 20;

		var count = 260;
		var positions = new Float32Array(count * 3);
		for (var i = 0; i < count; i++) {
			positions[i * 3] = (Math.random() - 0.5) * 40;
			positions[i * 3 + 1] = (Math.random() - 0.5) * 24;
			positions[i * 3 + 2] = (Math.random() - 0.5) * 20;
		}
		var geometry = new THREE.BufferGeometry();
		geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));

		var redMaterial = new THREE.PointsMaterial({ color: 0xe9204f, size: 0.14, transparent: true, opacity: 0.55 });
		var whiteMaterial = new THREE.PointsMaterial({ color: 0xf4f2f0, size: 0.08, transparent: true, opacity: 0.28 });

		var redPoints = new THREE.Points(geometry, redMaterial);
		var whitePoints = new THREE.Points(geometry.clone(), whiteMaterial);
		whitePoints.rotation.z = 0.6;
		scene.add(redPoints, whitePoints);

		var mouse = { x: 0, y: 0 };
		var frame = null;
		var running = false;

		function resize() {
			var rect = canvas.getBoundingClientRect();
			renderer.setSize(rect.width, rect.height, false);
			camera.aspect = rect.width / (rect.height || 1);
			camera.updateProjectionMatrix();
		}

		function onMouseMove(event) {
			mouse.x = (event.clientX / window.innerWidth - 0.5) * 2;
			mouse.y = (event.clientY / window.innerHeight - 0.5) * 2;
		}

		function tick() {
			if (!running) return;
			redPoints.rotation.y += 0.0006;
			whitePoints.rotation.y -= 0.0004;
			camera.position.x += (mouse.x * 2 - camera.position.x) * 0.02;
			camera.position.y += (-mouse.y * 1.2 - camera.position.y) * 0.02;
			camera.lookAt(scene.position);
			renderer.render(scene, camera);
			frame = window.requestAnimationFrame(tick);
		}

		function start() {
			if (running) return;
			running = true;
			resize();
			window.addEventListener("resize", resize);
			window.addEventListener("mousemove", onMouseMove);
			tick();
		}

		function stop() {
			running = false;
			if (frame) window.cancelAnimationFrame(frame);
			window.removeEventListener("resize", resize);
			window.removeEventListener("mousemove", onMouseMove);
		}

		return { start: start, stop: stop };
	}

	function init() {
		if (reduceMotion || lowPower || !supportsWebGL() || typeof window.THREE === "undefined") {
			return;
		}
		var hero = document.querySelector("[data-bp-hero-scene]");
		var canvas = hero && hero.querySelector("[data-bp-scene-canvas]");
		if (!hero || !canvas) return;

		var scene = buildScene(canvas);

		var observer = new IntersectionObserver(
			function (entries) {
				entries.forEach(function (entry) {
					if (entry.isIntersecting && document.visibilityState === "visible") {
						scene.start();
					} else {
						scene.stop();
					}
				});
			},
			{ threshold: 0.1 }
		);
		observer.observe(hero);

		document.addEventListener("visibilitychange", function () {
			if (document.visibilityState === "hidden") {
				scene.stop();
			} else if (hero.getBoundingClientRect().top < window.innerHeight && hero.getBoundingClientRect().bottom > 0) {
				scene.start();
			}
		});
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", init);
	} else {
		init();
	}
})();
