# Full site redesign + quote calculator — design spec

Date: 2026-09-28
Status: approved (conversational design), pending written-spec review

## 1. Background

The repo already contains a mostly-finished, unwired "redesign" design system
(`static/assets/css/redesign.css`, `static/assets/js/redesign.js`,
`templates/partials/quote-calculator.html`, `website/pricing.py`) plus a parked
migration for an `Enquiry` model (`wip-quote-calculator/migrations/`). None of
it is linked into any template today; the live site still runs the original
2021-era UIkit/jQuery/owl-carousel theme (`pr__*` classes).

This spec covers adopting the new dark editorial design system site-wide, in a
single pass, and finishing the quote-calculator feature end to end, plus
adding a motion/interaction layer (Lenis, GSAP, a scoped Three.js hero
background) to make the new design feel less static.

Decisions already made with the user (see chat log for full reasoning):

- **Single pass** — every template redone together, not phased.
- **Contact mechanism** — keep the existing, tested `ContactForm` /
  `ContactMessage` flow as the sitewide "get in touch" path (moves from a
  UIkit modal into an always-visible footer panel). The new `Enquiry` model
  powers a *separate*, richer `/quote/` flow. Nothing about `ContactForm`,
  `ContactView`, or its 17 tests changes.
- **Hero stats** — real founding year (2021) plus placeholder counts for the
  rest, clearly marked in code as placeholders for the client to update later.
- **Case studies** — no fabricated metrics/stack/scope copy for real client
  work. Templates degrade to existing fields (`name`, `description`,
  `category`, `tags`) wherever the new optional `Project` fields are blank.
- **Case study tabs** — not built this pass; the content model has no
  structured "chapters", and `redesign.js`'s tab code already no-ops with
  fewer than 2 tabs, so this is a safe deferral, not a bug.
- **Motion layer** — Lenis (smooth scroll) + GSAP/ScrollTrigger (reveal
  animations, stat count-up) site-wide; Three.js scoped to a subtle
  hero-background particle/line field only, lazy-loaded, paused off-screen,
  and skipped under `prefers-reduced-motion` or on low-end devices.

## 2. Data model changes

Add to `website/models.py`:

**`Service`** (new fields, all with sane defaults / `blank=True`):
`short_name`, `price_from` (`PositiveIntegerField`, default 0, 0 hides
pricing), `addon_factor` (`FloatField`, default 1.0), `is_retainer`
(default `False`), `timeline`, `deliverable`, `summary`, `highlights`
(newline-separated).

**`Project`** (new fields, all `blank=True`): `headline`, `metrics`
(newline-separated `"3.1×|Case intake per month"` pairs), `scope`, `stack`,
`summary`, `year`.

**New `Enquiry` model** (exact shape already drafted in
`wip-quote-calculator/migrations/0005_case_study_and_enquiry_fields.py`):
`name`, `business`, `email`, `phone`, `message`, `scope_kind`, `scope_size`,
`addons`, `estimate`, `preferred_slot`, `source` (`quote`/`service` choices),
`service` FK (nullable, `SET_NULL`), `handled` (bool), `created_at`.
`verbose_name_plural = "Enquiries"`, `ordering = ["-created_at"]`.

**Migrations**: move `wip-quote-calculator/migrations/*.py` back into
`website/migrations/`, renumbered `0007_case_study_and_enquiry_fields.py` and
`0008_seed_service_pricing.py` (dependency chain now starts from
`0006_contactmessage`, not `0004_seed_new_services`). Delete
`wip-quote-calculator/` once this lands. The pricing-seed data migration's
content is reused as-is — it already has real, well-written per-service copy.

## 3. Backend: quote / enquiry flow

- `website/forms.py`: add `EnquiryForm` (from `git stash show -p stash@{0}`)
  alongside the untouched `ContactForm`. Widgets add `bp-field` class,
  hidden inputs for the calculator-driven fields
  (`service`, `scope_kind`, `scope_size`, `addons`, `estimate`,
  `preferred_slot`, `source`).
- `website/admin.py`: register `Enquiry` similarly to `ContactMessageAdmin`
  (list display: name, business, service, estimate, created_at, handled;
  filter on `handled`/`source`/`created_at`; readonly on the submitted
  fields, editable `handled`).
- `website/views.py`: new `QuoteView`, modeled on `ContactView`'s pattern
  (honeypot not needed — this form has no public modal-spam surface the same
  way, but keep the same per-IP rate limit via `CONTACT_RATE_LIMIT`/cache key
  `"quote-form:{ip}"`, same store-then-best-effort-email approach, same
  JSON/redirect dual response). `GET` renders the quote page (calculator +
  full enquiry form); `POST` validates, saves, emails `CONTACT_EMAIL`, returns
  success/`bp-confirm` state.
- `website/urls.py`: add `path("quote/", QuoteView.as_view(), name="quote")`.
- `website/pricing.py` stays as-is; `QuoteView.get_context_data` (or a small
  context helper) feeds `quote_services` (from `Service.objects.all()`,
  mapped to the dicts `quote-calculator.html` expects — slug, label,
  price_from, addon_factor, is_retainer), `scope_sizes` (`pricing.SCOPE_SIZES`),
  and `quote_addons` (`pricing.QUOTE_ADDONS`) into every template that
  includes the calculator partial (home page + quote page + service detail
  short form).
- `templates/partials/quote-calculator.html` gets the missing
  `data-bp-input-kind` / `data-bp-input-size` / `data-bp-input-addons` /
  `data-bp-input-estimate` hidden `<input>` elements `redesign.js` already
  looks for, wired to `EnquiryForm`'s hidden fields, so a selection actually
  reaches the submitted form.

## 4. Frontend: shared shell

- `base.html`: `<body class="bp">`. Drop
  `normalize.min.css`, `pr.animation.css`, `owl.carousel.min.css`,
  `uikit.min.css`, `pixeicons.css`, `jquery.min.js`, `anime.min.js`,
  `pr.animation.js`, `uikit.min.js`, `owl.carousel.min.js`, `validate.js`,
  `main.js`. Keep `fonts.css` (already defines "Trade Gothic"/"Avant Grade",
  which is exactly what `redesign.css` expects — no new font loading needed)
  and `style.css`'s favicon/meta bits as needed. Add `redesign.css`,
  `redesign.js`, and the new motion-layer scripts (§7). AdSense tag is left
  untouched — out of scope for this redesign.
- `templates/partials/header.html` → `bp-header`/`bp-nav`: Home, About,
  Services, Work, Blog, "Contact" (anchor-scrolls to the footer panel,
  replacing the old modal toggle), plus a primary "Get a quote" `bp-btn`
  linking to `/quote/`. Burger + `bp-mobile-nav` partial for small screens,
  driven by the existing `data-bp-burger`/`data-bp-mobile-nav` hooks in
  `redesign.js` — no template-side JS needed.
- `templates/partials/footer.html` → `bp-footer` (contact links, socials,
  copyright) with the existing `ContactForm` rendered inline as a compact
  `bp-field`/`bp-btn` panel — no modal, always visible. This replaces
  `templates/partials/contact_form.html`'s UIkit full-screen modal; the
  `ContactView`/`ContactForm` Python code is untouched, only the template
  markup around it changes. The AJAX submit JS in `main.js` that currently
  drives this form's UX will need a small vanilla replacement appended to
  `redesign.js` (submit via `fetch`, show `bp-errors`/success inline) since
  `main.js` is being removed.
- `templates/partials/messages.html` → `bp-messages` bar.
- New shared partial `templates/partials/cta-bar.html` → sticky `bp-ctabar`
  linking to `/quote/`, included near the end of `base.html` content pages
  (not needed on the quote page itself, to avoid a CTA bar promoting its own
  page).

## 5. Frontend: page-by-page

**Home** (`home.html`): hero (headline + CTA, motion-layer background) →
stats bar (`2021 · Founded`, placeholder project/client/service counts,
flagged with an inline comment) → 3-up "why us" features (existing copy,
reused verbatim) → services grid (`bp-service-card`, real `Service` data) →
work grid (`bp-work-grid`, real `Project` data, degrading per §1) →
testimonial (`bp-testimonial`, existing Brian Josh quote reused verbatim) →
quote calculator (`quote-calculator.html`) → footer.

**Services** (`service-list.html`, `service-single.html`): list as
`bp-accordion` (number, name, one-line pitch, price-from, expands to
`summary`/`highlights`/`timeline`/`deliverable`). Detail: hero +
`formatted_markdown` in `bp-prose`, sidebar with other services plus a short
enquiry form preselecting this service (`data-bp-preselect="{{ object.slug }}"`
on the calculator).

**Work / projects** (`project-list.html`, `project-single.html`): list as
`bp-work-grid`/tiles. Detail as `bp-case-layout`: main column is
`formatted_markdown` in `bp-prose` plus the existing image gallery re-themed
with the offset/shadow-card treatment; sidebar `bp-deflist` for
client/category/tags, plus year/scope/stack when present. No chapter tabs
(§1).

**About** (`about.html`): hero + `bp-split`/`bp-list-block` for the existing
"who we are / what we do / philosophy" copy, process steps if useful, sidebar
service list. Slideshow images become a simple `bp-work-grid`-style tile row
(no JS slideshow dependency to replace).

**Blog** (`blog-page.html`, `blog-single.html`): list as `bp-post-card` grid.
Detail as `bp-prose` body with `bp-post-meta`, related posts grid.

**Quote page** (new `templates/quote.html`): full calculator feeding the
hidden `EnquiryForm` inputs, submitted via `QuoteView`. Success state renders
`bp-confirm` + `bp-nextsteps` (what happens next / when we'll call /
alternative contact). Uses `data-bp-steps` if a multi-step flow proves
useful, but a single-page form is an acceptable v1 (the JS supports steps if
we want to promote to multi-step without further backend changes).

## 6. Content-fallback rules (no fabricated business content)

- `Project`: `headline` falls back to `name`; `summary` falls back to a
  truncated `description`; `metrics`/`scope`/`stack`/`year` sections are
  simply omitted from the template when blank (not rendered as empty boxes).
- `Service`: pricing/timeline/deliverable/highlights are already seeded by
  the migration for all 6 current services, so no fallback needed there
  today — but any *future* service created without these fields should
  still render sensibly (price-from hidden when 0, as the model's own
  help text already says).
- Hero stats: hardcoded placeholder values with a `{# TODO: replace with
  real figures #}` template comment (not pulled from the DB — no model
  exists for "site-wide stats" and adding one is out of scope here).

## 7. Motion / interaction layer

- **Lenis** (smooth scroll) and **GSAP** + **ScrollTrigger** loaded from
  CDN in `base.html`, after `redesign.js`. Specific versions pinned (latest
  stable at implementation time; plan will record exact CDN URLs).
- A new `static/assets/js/motion.js` (vanilla, no build step) wires:
  - Lenis instance driving scroll, synced to `ScrollTrigger.update` per the
    standard Lenis+GSAP integration recipe.
  - Section entrance animations: headings/cards fade+rise on scroll into
    view, staggered per grid (`bp-service-card`, `bp-work-card`,
    `bp-studio-card`, etc.).
  - Count-up animation for the hero stats numbers.
  - All of the above skipped entirely under `prefers-reduced-motion:
    reduce` (matches `redesign.css`'s own existing reduced-motion rule) —
    content renders fully visible, unanimated, immediately.
- **Three.js**, scoped strictly to the hero background:
  - A new `static/assets/js/hero-scene.js`, loaded only on pages with a
    `[data-bp-hero-scene]` hero (home page only, or all heroes — decide at
    implementation time based on how it looks; default is home page only to
    start).
  - Subtle drifting line/particle field in the dark palette with
    `--bp-red` accents, low opacity, gentle parallax on mouse move. No
    text/logo/complex geometry.
  - Instantiated lazily via `IntersectionObserver` only once the hero
    enters the viewport; the render loop pauses via
    `document.visibilitychange`/`IntersectionObserver` when the hero is
    scrolled past or the tab is backgrounded.
  - Skipped entirely (falls back to the existing static hero image +
    gradient scrim, zero visual regression) when
    `prefers-reduced-motion: reduce`, or when a light capability check
    (e.g. `navigator.hardwareConcurrency` below a small threshold, or WebGL
    context creation failing) suggests a low-end device.
  - Three.js loaded from CDN as an ES module or UMD build, whichever keeps
    the no-build-step constraint simplest; plan will record the exact
    approach.

## 8. Testing

- All 17 existing `ContactForm`/page tests in `website/tests.py` keep
  passing unmodified — they test behavior, not the removed CSS/JS, except
  `test_no_relative_asset_paths` which will need its asset-path assertions
  reviewed against the new template output (same rules, new markup).
- New tests for `EnquiryForm`/`QuoteView`, mirroring the existing
  `ContactFormTests` structure: valid submission stores + emails, invalid
  submission returns errors, rate limiting, CSRF required, GET renders the
  calculator with services/scope/addons in context.
- New/updated `test_list_pages`-style coverage for the redesigned templates
  (200 status, key content present) — no behavior change expected, but
  confirms nothing 500s after the full template swap.
- Manual visual QA pass across every page type once built, using gstack's
  `/qa` or `/browse` skill (per house convention — not raw browser
  automation), checking: layout at desktop/tablet/mobile widths, reduced-motion
  fallback, hero scene degrading gracefully with JS/WebGL disabled, and the
  full quote-calculator → submission → confirmation flow.

## 9. Rollout

Single pass, as directed: all template and backend changes land together.
`wip-quote-calculator/` is deleted once its migrations are merged into
`website/migrations/`. No feature flag / gradual rollout — this is pre-launch
review work happening directly on top of the already-fixed `master` branch
state (see prior conversation: the forms.py merge conflict and broken
migrations were fixed separately and are not part of this spec).

## 10. Out of scope

- Rewriting service/project/blog copy content itself (only templates and
  presentation change; existing admin content is reused).
- A CMS-editable "site stats" model — the hero stats are hardcoded
  placeholders per §6.
- Multi-step quote flow UI (steps 1/2/3) — v1 ships as a single-page form;
  the JS (`initSteps`) already supports promoting to multi-step later
  without backend changes.
- Case-study chapter tabs (§1).
- Any change to `ContactForm`/`ContactMessage`/`ContactView` Python logic or
  its test suite.
