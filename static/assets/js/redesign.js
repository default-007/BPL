/* BakPage Labs — redesign behaviour
   1. Mobile navigation
   2. Case study chapter tabs
   3. Quote calculator (home widget + enquiry step 1)
   4. Enquiry step flow
   Everything degrades to plain HTML when JavaScript is unavailable. */
(function () {
	"use strict";

	document.documentElement.classList.add("bp-js");

	var $ = function (selector, scope) {
		return (scope || document).querySelector(selector);
	};
	var $$ = function (selector, scope) {
		return Array.prototype.slice.call((scope || document).querySelectorAll(selector));
	};

	/* 1. Mobile navigation
	--------------------------------------------------- */
	function initNav() {
		var burger = $("[data-bp-burger]");
		var nav = $("[data-bp-mobile-nav]");
		if (!burger || !nav) return;

		burger.addEventListener("click", function () {
			var open = nav.classList.toggle("is-open");
			burger.setAttribute("aria-expanded", open ? "true" : "false");
		});
	}

	/* 2. Case study chapter tabs
	--------------------------------------------------- */
	function initTabs() {
		$$("[data-bp-tabs]").forEach(function (group) {
			var tabs = $$("[data-bp-tab]", group);
			var panels = $$("[data-bp-panel]", group);
			if (tabs.length < 2) return;

			function select(id) {
				tabs.forEach(function (tab) {
					var active = tab.getAttribute("data-bp-tab") === id;
					tab.classList.toggle("is-active", active);
					tab.setAttribute("aria-selected", active ? "true" : "false");
				});
				panels.forEach(function (panel) {
					panel.hidden = panel.getAttribute("data-bp-panel") !== id;
				});
			}

			tabs.forEach(function (tab) {
				tab.addEventListener("click", function () {
					select(tab.getAttribute("data-bp-tab"));
				});
			});

			select(tabs[0].getAttribute("data-bp-tab"));
		});
	}

	/* 3. Quote calculator
	--------------------------------------------------- */
	function money(value) {
		return value.toLocaleString("en-KE");
	}

	function initCalculators() {
		$$("[data-bp-calc]").forEach(function (calc) {
			var kinds = $$("[data-bp-kind]", calc);
			var sizes = $$("[data-bp-size]", calc);
			var addons = $$("[data-bp-addon]", calc);
			if (!kinds.length || !sizes.length) return;

			var out = {
				estimate: $("[data-bp-estimate]", calc),
				timeline: $("[data-bp-timeline]", calc),
				note: $("[data-bp-note]", calc),
				summary: $("[data-bp-summary]", calc)
			};
			var fields = {
				kind: $("[data-bp-input-kind]", calc),
				size: $("[data-bp-input-size]", calc),
				addons: $("[data-bp-input-addons]", calc),
				estimate: $("[data-bp-input-estimate]", calc)
			};

			var state = {
				kind: kinds[0],
				size: sizes[Math.min(1, sizes.length - 1)],
				addons: addons.filter(function (addon) {
					return addon.hasAttribute("data-bp-default");
				})
			};

			function num(el, attr, fallback) {
				var value = parseFloat(el.getAttribute(attr));
				return isNaN(value) ? fallback : value;
			}

			function render() {
				var base = num(state.kind, "data-base", 0);
				var factor = num(state.kind, "data-factor", 1);
				var retainer = state.kind.getAttribute("data-retainer") === "true";
				var mult = num(state.size, "data-mult", 1);
				var weeks = state.size.getAttribute("data-weeks") || "";
				var extra = state.addons.reduce(function (total, addon) {
					return total + num(addon, "data-add", 0);
				}, 0);

				var low = Math.round((base * mult + extra * factor) / 10) * 10;
				var high = Math.round((low * 1.35) / 5) * 5;
				var estimate = base
					? "KES " + money(low) + "k – " + money(high) + "k" + (retainer ? " / mo" : "")
					: "On enquiry";

				kinds.forEach(function (el) {
					el.classList.toggle("is-active", el === state.kind);
					el.setAttribute("aria-pressed", el === state.kind ? "true" : "false");
				});
				sizes.forEach(function (el) {
					el.classList.toggle("is-active", el === state.size);
					el.setAttribute("aria-pressed", el === state.size ? "true" : "false");
				});
				addons.forEach(function (el) {
					var on = state.addons.indexOf(el) !== -1;
					el.classList.toggle("is-active", on);
					el.setAttribute("aria-pressed", on ? "true" : "false");
				});

				var kindLabel = state.kind.getAttribute("data-label") || "";
				var sizeLabel = state.size.getAttribute("data-label") || "";

				if (out.estimate) out.estimate.textContent = estimate;
				if (out.timeline) {
					out.timeline.textContent = retainer
						? "Rolling, cancel any month"
						: weeks + " to launch";
				}
				if (out.note) {
					out.note.textContent = retainer
						? "Includes a prioritised roadmap, architecture review, vendor decisions and weekly advisory — cancel any month."
						: kindLabel +
						  ", " +
						  sizeLabel.toLowerCase() +
						  " scope. Includes discovery, two design directions, build in weekly sprints, launch and 30 days of fixes.";
				}
				if (out.summary) {
					out.summary.textContent = kindLabel + " · " + estimate;
				}

				if (fields.kind) fields.kind.value = state.kind.getAttribute("data-value") || kindLabel;
				if (fields.size) fields.size.value = sizeLabel;
				if (fields.estimate) fields.estimate.value = estimate;
				if (fields.addons) {
					fields.addons.value = state.addons
						.map(function (addon) {
							return addon.getAttribute("data-label") || "";
						})
						.join(", ");
				}
			}

			kinds.forEach(function (el) {
				el.addEventListener("click", function () {
					state.kind = el;
					render();
				});
			});
			sizes.forEach(function (el) {
				el.addEventListener("click", function () {
					state.size = el;
					render();
				});
			});
			addons.forEach(function (el) {
				el.addEventListener("click", function () {
					var at = state.addons.indexOf(el);
					if (at === -1) {
						state.addons.push(el);
					} else {
						state.addons.splice(at, 1);
					}
					render();
				});
			});

			var preselect = calc.getAttribute("data-bp-preselect");
			if (preselect) {
				kinds.forEach(function (el) {
					if (el.getAttribute("data-value") === preselect) state.kind = el;
				});
			}

			render();
		});
	}

	/* 4. Enquiry step flow
	--------------------------------------------------- */
	function initSteps() {
		var flow = $("[data-bp-steps]");
		if (!flow) return;

		var steps = $$("[data-bp-step]", flow);
		var marks = $$("[data-bp-stepmark]", flow);
		var titles = $$("[data-bp-steptitle]", flow);
		if (steps.length < 2) return;

		function show(index) {
			steps.forEach(function (step) {
				step.hidden = parseInt(step.getAttribute("data-bp-step"), 10) !== index;
			});
			marks.forEach(function (mark) {
				mark.classList.toggle(
					"is-done",
					parseInt(mark.getAttribute("data-bp-stepmark"), 10) <= index
				);
			});
			titles.forEach(function (title) {
				title.hidden = parseInt(title.getAttribute("data-bp-steptitle"), 10) !== index;
			});
			window.scrollTo(0, 0);
		}

		$$("[data-bp-next]", flow).forEach(function (button) {
			button.addEventListener("click", function () {
				show(parseInt(button.getAttribute("data-bp-next"), 10));
			});
		});
		$$("[data-bp-back]", flow).forEach(function (button) {
			button.addEventListener("click", function () {
				show(parseInt(button.getAttribute("data-bp-back"), 10));
			});
		});

		var start = parseInt(flow.getAttribute("data-bp-steps"), 10);
		show(isNaN(start) ? 1 : start);
	}

	/* 5. Sitewide contact form (progressive enhancement)
	--------------------------------------------------- */
	function initContactForm() {
		var form = $("[data-bp-contact-form]");
		if (!form) return;
		var status = $(".pr__contact__status", form);

		form.addEventListener("submit", function (event) {
			event.preventDefault();
			var data = new FormData(form);
			fetch(form.getAttribute("action"), {
				method: "POST",
				body: data,
				headers: { "X-Requested-With": "XMLHttpRequest" }
			})
				.then(function (response) {
					return response.json().then(function (payload) {
						return { ok: response.ok, payload: payload };
					});
				})
				.then(function (result) {
					if (status) {
						status.textContent = result.payload.message;
						status.classList.toggle("bp-form-status--error", !result.ok);
					}
					if (result.ok) form.reset();
				})
				.catch(function () {
					if (status) status.textContent = "Something went wrong. Please try again.";
				});
		});
	}

	function init() {
		initNav();
		initTabs();
		initCalculators();
		initSteps();
		initContactForm();
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", init);
	} else {
		init();
	}
})();
