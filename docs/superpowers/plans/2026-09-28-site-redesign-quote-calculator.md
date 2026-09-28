# Site redesign + quote calculator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the site's legacy UIkit/jQuery theme with the already-drafted dark "redesign" design system across every page, and finish the quote-calculator feature end to end (data model, form, view, templates), without touching the existing, tested `ContactForm` flow.

**Architecture:** A shared `base.html` shell now owns the header/nav/footer/CTA-bar/scripts (previously duplicated per page); every page template becomes just its `{% block content %}`. A new `Enquiry` model + `EnquiryForm` + `QuoteView` power a separate `/quote/` flow alongside the untouched `ContactForm`/`ContactView`. A motion layer (Lenis + GSAP) adds scroll-driven reveals site-wide; a Three.js particle field is scoped strictly to the home page hero background, lazy-loaded and fully gated behind `prefers-reduced-motion`/WebGL support checks.

**Tech Stack:** Django 5.2 (existing), vanilla JS (no build step), Lenis + GSAP/ScrollTrigger + Three.js from CDN.

**Spec:** `docs/superpowers/specs/2026-09-28-site-redesign-quote-calculator-design.md`

## Global Constraints

- Every existing test in `website/tests.py` (17 tests, `ContactForm`/`ContactMessage`/`ContactView`) must keep passing, unmodified in intent — only markup assertions may need updated expected strings if the DOM structure around them changes, never the behavior under test.
- No fabricated business metrics/content. Hero stats use hardcoded placeholders marked with a `{# TODO #}` comment; `Project`/`Service` template fields degrade gracefully to existing fields when blank — never render an empty label/box.
- No build step — every new JS/CSS file is vanilla and loaded via `<script src>`/`<link>`, Lenis/GSAP/Three.js via CDN `<script>` tags.
- All motion (Lenis, GSAP reveals, stat counters, the Three.js hero scene) must no-op under `prefers-reduced-motion: reduce`, leaving content fully visible and unanimated.
- The Three.js hero scene loads only on the home page, only once its hero enters the viewport (`IntersectionObserver`), pauses when scrolled away or the tab is hidden, and never loads at all without WebGL support.
- Migration `0007_case_study_and_enquiry_fields.py` depends on `0006_contactmessage` (not `0004_seed_new_services` as in the original drafted file) — the field-length `AlterField` operations already applied by `0005_field_lengths.py` are dropped from this migration since they'd be redundant.
- `wip-quote-calculator/` is deleted once its migrations are merged in (final task).
- Reuse existing real page copy; only replace copy that is obvious unpublished lorem-ipsum-style filler left over from the original theme template (flagged inline where it happens).

## Review Focus

- Blank optional `Project`/`Service` fields (a project or service created via admin without filling in the new redesign fields) must never render empty headings, dashes, or broken layout — Task 14 adds an explicit test for this.
- A quote submission where JavaScript failed to run (so the calculator's hidden inputs are all empty) must still validate and save — Task 5 tests this directly.
- The quote form must be rate-limited per IP and require CSRF, exactly like the contact form — Task 5 tests both.
- Applying every migration from a fresh database must succeed in one pass with no manual `--merge` step, and must seed exactly six services with real pricing data — Task 2 tests this.
- Swapping the entire template/asset stack in `base.html` (Task 9) must not silently break any existing page — the full existing suite is re-run as that task's own test, not just at the very end.

---

## Task 1: Data model — `Service`/`Project` fields and the `Enquiry` model

**Files:**
- Modify: `website/models.py`
- Create: `website/migrations/0007_case_study_and_enquiry_fields.py`
- Test: `website/tests.py`

**Interfaces:**
- Produces: `Service.short_name`, `.summary`, `.highlights`, `.timeline`, `.deliverable`, `.price_from`, `.addon_factor`, `.is_retainer`; `Project.headline`, `.summary`, `.scope`, `.stack`, `.year`, `.metrics`, `.metrics_list` (property); `Enquiry` model with fields `name`, `business`, `email`, `phone`, `message`, `service` (FK to `Service`, nullable), `scope_kind`, `scope_size`, `addons`, `estimate`, `preferred_slot`, `source` (`"quote"`/`"service"`), `handled`, `created_at`.

- [ ] **Step 1: Write the failing tests**

Add to `website/tests.py` (near the top, alongside existing imports add `Enquiry`):

```python
from .models import Blog, Category, ContactMessage, Enquiry, Project, Service
```

Add a new test class:

```python
class RedesignModelTests(TestCase):
    def test_service_has_pricing_fields_with_sane_defaults(self):
        service = Service.objects.create(name="Test service", slug="test-service")
        self.assertEqual(service.price_from, 0)
        self.assertEqual(service.addon_factor, 1.0)
        self.assertFalse(service.is_retainer)
        self.assertEqual(service.short_name, "")
        self.assertEqual(service.highlights, "")

    def test_project_has_case_study_fields_with_sane_defaults(self):
        category = Category.objects.create(name="Branding")
        project = Project.objects.create(
            name="Test project", image="test.png", description="x",
            category=category, slug="test-project",
        )
        self.assertEqual(project.headline, "")
        self.assertEqual(project.metrics, "")
        self.assertEqual(project.metrics_list, [])

    def test_project_metrics_list_parses_value_and_label(self):
        category = Category.objects.create(name="Branding")
        project = Project.objects.create(
            name="Test project", image="test.png", description="x",
            category=category, slug="test-project-2",
            metrics="3.1×|Case intake per month\n40%|Faster onboarding",
        )
        self.assertEqual(
            project.metrics_list,
            [("3.1×", "Case intake per month"), ("40%", "Faster onboarding")],
        )

    def test_enquiry_can_be_created_with_only_required_fields(self):
        enquiry = Enquiry.objects.create(email="lead@example.com", message="Hello")
        self.assertEqual(enquiry.source, "quote")
        self.assertFalse(enquiry.handled)
        self.assertIsNone(enquiry.service)
        self.assertEqual(str(enquiry), "lead@example.com (Quote flow)")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test website.tests.RedesignModelTests -v 2`
Expected: FAIL — `ImportError: cannot import name 'Enquiry'` (or `AttributeError`/`FieldError` once the import is fixed manually for the check).

- [ ] **Step 3: Add the fields and the `Enquiry` model**

In `website/models.py`, add the new fields to `Service` (after `order = models.PositiveIntegerField(default=0)`):

```python
    # Quote calculator / redesign fields.
    short_name = models.CharField(
        max_length=60, blank=True,
        help_text="Used in running copy, e.g. 'AI & automation'.",
    )
    summary = models.TextField(
        blank=True,
        help_text="Plain-text pitch shown when the service is opened on the services page.",
    )
    highlights = models.TextField(blank=True, help_text="One highlight per line.")
    timeline = models.CharField(max_length=60, blank=True, help_text="e.g. '4–8 weeks'.")
    deliverable = models.CharField(max_length=120, blank=True, help_text="What the client ends up with.")
    price_from = models.PositiveIntegerField(
        default=0,
        help_text="Indicative starting price in thousands of KES. 0 hides pricing.",
    )
    addon_factor = models.FloatField(
        default=1.0,
        help_text="How strongly quote add-ons move this service's estimate.",
    )
    is_retainer = models.BooleanField(default=False, help_text="Priced monthly rather than per project.")
```

Add the new fields to `Project` (after `tags = TaggableManager()`), plus the `metrics_list` property:

```python
    # Case-study fields for the redesigned work pages.
    headline = models.CharField(
        max_length=200, blank=True,
        help_text="Case study headline. Falls back to the project name.",
    )
    summary = models.TextField(blank=True, help_text="Standfirst shown under the case study headline.")
    scope = models.CharField(max_length=120, blank=True, help_text="e.g. 'Platform, brand, training'.")
    stack = models.CharField(max_length=120, blank=True, help_text="e.g. 'Django, Postgres'.")
    year = models.CharField(max_length=20, blank=True)
    metrics = models.TextField(
        blank=True,
        help_text='One result per line, as "3.1×|Case intake per month".',
    )

    @property
    def metrics_list(self):
        """Parsed ``(value, label)`` pairs from ``metrics``, one per line."""
        pairs = []
        for line in self.metrics.splitlines():
            line = line.strip()
            if not line:
                continue
            value, _, label = line.partition("|")
            pairs.append((value.strip(), label.strip()))
        return pairs
```

Add the `Enquiry` model after `ContactMessage`:

```python
class Enquiry(models.Model):
    """A lead captured through the quote calculator or a service's short enquiry form."""

    SOURCE_CHOICES = [
        ("quote", "Quote flow"),
        ("service", "Service page"),
    ]

    name = models.CharField(max_length=120, blank=True)
    business = models.CharField(max_length=120, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    message = models.TextField()
    service = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, blank=True, related_name="enquiries",
    )
    scope_kind = models.CharField(max_length=120, blank=True)
    scope_size = models.CharField(max_length=120, blank=True)
    addons = models.CharField(max_length=200, blank=True)
    estimate = models.CharField(max_length=60, blank=True)
    preferred_slot = models.CharField(max_length=60, blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="quote")
    handled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Enquiries"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name or self.email} ({self.get_source_display()})"
```

- [ ] **Step 4: Write the migration**

Create `website/migrations/0007_case_study_and_enquiry_fields.py`:

```python
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("website", "0006_contactmessage"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="headline",
            field=models.CharField(blank=True, help_text="Case study headline. Falls back to the project name.", max_length=200),
        ),
        migrations.AddField(
            model_name="project",
            name="metrics",
            field=models.TextField(blank=True, help_text='One result per line, as "3.1×|Case intake per month".'),
        ),
        migrations.AddField(
            model_name="project",
            name="scope",
            field=models.CharField(blank=True, help_text="e.g. 'Platform, brand, training'.", max_length=120),
        ),
        migrations.AddField(
            model_name="project",
            name="stack",
            field=models.CharField(blank=True, help_text="e.g. 'Django, Postgres'.", max_length=120),
        ),
        migrations.AddField(
            model_name="project",
            name="summary",
            field=models.TextField(blank=True, help_text="Standfirst shown under the case study headline."),
        ),
        migrations.AddField(
            model_name="project",
            name="year",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="service",
            name="addon_factor",
            field=models.FloatField(default=1.0, help_text="How strongly quote add-ons move this service's estimate."),
        ),
        migrations.AddField(
            model_name="service",
            name="deliverable",
            field=models.CharField(blank=True, help_text="What the client ends up with.", max_length=120),
        ),
        migrations.AddField(
            model_name="service",
            name="highlights",
            field=models.TextField(blank=True, help_text="One highlight per line."),
        ),
        migrations.AddField(
            model_name="service",
            name="is_retainer",
            field=models.BooleanField(default=False, help_text="Priced monthly rather than per project."),
        ),
        migrations.AddField(
            model_name="service",
            name="price_from",
            field=models.PositiveIntegerField(default=0, help_text="Indicative starting price in thousands of KES. 0 hides pricing."),
        ),
        migrations.AddField(
            model_name="service",
            name="short_name",
            field=models.CharField(blank=True, help_text="Used in running copy, e.g. 'AI & automation'.", max_length=60),
        ),
        migrations.AddField(
            model_name="service",
            name="summary",
            field=models.TextField(blank=True, help_text="Plain-text pitch shown when the service is opened on the services page."),
        ),
        migrations.AddField(
            model_name="service",
            name="timeline",
            field=models.CharField(blank=True, help_text="e.g. '4–8 weeks'.", max_length=60),
        ),
        migrations.CreateModel(
            name="Enquiry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(blank=True, max_length=120)),
                ("business", models.CharField(blank=True, max_length=120)),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(blank=True, max_length=40)),
                ("message", models.TextField()),
                ("scope_kind", models.CharField(blank=True, max_length=120)),
                ("scope_size", models.CharField(blank=True, max_length=120)),
                ("addons", models.CharField(blank=True, max_length=200)),
                ("estimate", models.CharField(blank=True, max_length=60)),
                ("preferred_slot", models.CharField(blank=True, max_length=60)),
                ("source", models.CharField(choices=[("quote", "Quote flow"), ("service", "Service page")], default="quote", max_length=20)),
                ("handled", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("service", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="enquiries", to="website.service")),
            ],
            options={
                "verbose_name_plural": "Enquiries",
                "ordering": ["-created_at"],
            },
        ),
    ]
```

- [ ] **Step 5: Run `makemigrations --check` and the tests**

Run: `python manage.py makemigrations --check --dry-run`
Expected: `No changes detected`

Run: `python manage.py test website.tests.RedesignModelTests -v 2`
Expected: PASS (4 tests)

Run: `python manage.py test website -v 2`
Expected: all previously-existing tests still PASS.

- [ ] **Step 6: Commit**

```bash
git add website/models.py website/migrations/0007_case_study_and_enquiry_fields.py website/tests.py
git commit -m "Add Enquiry model and redesign fields on Service/Project"
```

---

## Task 2: Seed-data migration for service pricing

**Files:**
- Create: `website/migrations/0008_seed_service_pricing.py`
- Test: `website/tests.py`

**Interfaces:**
- Consumes: `Service` model from Task 1.
- Produces: six `Service` rows with `short_name`/`price_from`/`addon_factor`/`is_retainer`/`timeline`/`deliverable`/`summary`/`highlights` populated (real copy, not placeholders).

- [ ] **Step 1: Write the failing test**

Add to `website/tests.py`, inside the existing `PageTests` class (it already has `test_services_seeded_by_migration`):

```python
    def test_service_pricing_seeded_by_migration(self):
        service = Service.objects.get(slug="ai-automation")
        self.assertEqual(service.price_from, 85)
        self.assertEqual(service.short_name, "AI & automation")
        self.assertIn("WhatsApp & chat agents", service.highlights)

        advisory = Service.objects.get(slug="tech-advisory")
        self.assertTrue(advisory.is_retainer)
        self.assertEqual(advisory.price_from, 45)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test website.tests.PageTests.test_service_pricing_seeded_by_migration -v 2`
Expected: FAIL — `Service matching query does not exist` or `price_from` is `0` (migration not applied yet).

- [ ] **Step 3: Write the migration**

Create `website/migrations/0008_seed_service_pricing.py`:

```python
"""Fill in the open pricing the redesigned services screen shows."""

from django.db import migrations


SERVICE_PRICING = {
    "ai-automation": {
        "short_name": "AI & automation",
        "price_from": 85,
        "addon_factor": 1.1,
        "timeline": "4–8 weeks",
        "deliverable": "Agents live in your workflow",
        "summary": (
            "Custom AI agents that handle the repetitive, high-volume work your team shouldn't "
            "be doing manually: WhatsApp and chat agents running 24/7, workflow automation for "
            "invoices and reporting, M-Pesa and CRM integrations, and document processing that "
            "reads receipts, forms and PDFs on its own."
        ),
        "highlights": [
            "WhatsApp & chat agents",
            "Workflow automation",
            "AI-powered integrations",
            "Document & data processing",
        ],
    },
    "software-development": {
        "short_name": "custom software",
        "price_from": 180,
        "addon_factor": 1.35,
        "timeline": "8–14 weeks",
        "deliverable": "MVP in production",
        "summary": (
            "Production-grade software, not tech demos. MVPs that test your market hypothesis in "
            "weeks, multi-tenant SaaS platforms with billing and user management, internal tools "
            "that replace spreadsheets, and cross-platform mobile apps that work offline and "
            "speak M-Pesa."
        ),
        "highlights": [
            "MVPs & prototypes",
            "SaaS platforms",
            "Internal tools & dashboards",
            "Mobile apps & APIs",
        ],
    },
    "digital-transformation": {
        "short_name": "digital transformation",
        "price_from": 120,
        "addon_factor": 1.15,
        "timeline": "6–12 weeks",
        "deliverable": "Systems your team actually uses",
        "summary": (
            "Most SMEs run critical operations on WhatsApp groups, paper ledgers and spreadsheets "
            "held together with hope. We digitise systematically — automated M-Pesa "
            "reconciliation, ERP/CRM set up around how you really work, inventory and approval "
            "chains off paper, and a move off fragile local servers."
        ),
        "highlights": [
            "Payment & M-Pesa integration",
            "ERP & CRM setup",
            "Process digitisation",
            "Cloud migration",
        ],
    },
    "web-design": {
        "short_name": "web & product design",
        "price_from": 65,
        "addon_factor": 1.0,
        "timeline": "3–8 weeks",
        "deliverable": "Web app + design system",
        "summary": (
            "Your web presence is a business tool, not a brochure. Data-driven web applications "
            "with accounts and dashboards, eCommerce with M-Pesa checkout and inventory sync, "
            "UI/UX grounded in user research, and landing pages built to convert with tracking "
            "baked in."
        ),
        "highlights": [
            "Web applications",
            "E-commerce & marketplaces",
            "UI/UX design",
            "Landing pages & funnels",
        ],
    },
    "data-analytics": {
        "short_name": "data & BI",
        "price_from": 75,
        "addon_factor": 0.95,
        "timeline": "4–8 weeks",
        "deliverable": "Live dashboard + auto reports",
        "summary": (
            "You already have the data — sales, customers, M-Pesa, traffic. We connect the "
            "scattered sources into one reliable view, build dashboards that answer “how are we "
            "doing?” in under 30 seconds, and automate the reports nobody wants to assemble by "
            "hand."
        ),
        "highlights": [
            "Custom dashboards",
            "Automated reporting",
            "Data pipeline setup",
            "AI-powered insights",
        ],
    },
    "tech-advisory": {
        "short_name": "tech advisory",
        "price_from": 45,
        "addon_factor": 0.6,
        "is_retainer": True,
        "timeline": "One-off or monthly",
        "deliverable": "Roadmap, audit, hiring support",
        "summary": (
            "Hands-on tech strategy on a fractional basis: prioritised roadmaps tied to business "
            "goals, honest architecture and code audits, unbiased build-vs-buy calls, help hiring "
            "and structuring your technical team, and technical documentation for investors and "
            "due diligence."
        ),
        "highlights": [
            "Tech strategy & roadmaps",
            "Architecture & code audits",
            "Vendor & tool selection",
            "Team building & hiring",
        ],
    },
}


def seed_pricing(apps, schema_editor):
    Service = apps.get_model("website", "Service")
    for slug, data in SERVICE_PRICING.items():
        service = Service.objects.filter(slug=slug).first()
        if service is None:
            continue
        service.short_name = data["short_name"]
        service.price_from = data["price_from"]
        service.addon_factor = data["addon_factor"]
        service.is_retainer = data.get("is_retainer", False)
        service.timeline = data["timeline"]
        service.deliverable = data["deliverable"]
        service.summary = data["summary"]
        service.highlights = "\n".join(data["highlights"])
        service.save()


def clear_pricing(apps, schema_editor):
    Service = apps.get_model("website", "Service")
    Service.objects.filter(slug__in=SERVICE_PRICING).update(
        short_name="",
        price_from=0,
        addon_factor=1.0,
        is_retainer=False,
        timeline="",
        deliverable="",
        summary="",
        highlights="",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("website", "0007_case_study_and_enquiry_fields"),
    ]

    operations = [
        migrations.RunPython(seed_pricing, clear_pricing),
    ]
```

- [ ] **Step 4: Run the test**

Run: `python manage.py test website -v 2`
Expected: all tests PASS, including the new one.

- [ ] **Step 5: Commit**

```bash
git add website/migrations/0008_seed_service_pricing.py website/tests.py
git commit -m "Seed real pricing/copy for the six services"
```

---

## Task 3: `EnquiryForm`

**Files:**
- Modify: `website/forms.py`
- Test: `website/tests.py`

**Interfaces:**
- Consumes: `Enquiry` model (Task 1).
- Produces: `EnquiryForm` (Django `ModelForm`), fields `name`, `business`, `email`, `phone`, `message`, `service`, `scope_kind`, `scope_size`, `addons`, `estimate`, `preferred_slot`, `source`; non-hidden widgets get `class="bp-field"`.

- [ ] **Step 1: Write the failing tests**

Add to `website/tests.py` (import `EnquiryForm` alongside the existing `ContactForm` import):

```python
from .forms import ContactForm, EnquiryForm
```

```python
class EnquiryFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.service = Service.objects.create(name="AI & automation", slug="ai-automation")

    def valid_data(self, **overrides):
        data = {
            "name": "Jane Wanjiku",
            "business": "Jane's Shop",
            "email": "jane@example.com",
            "phone": "0700000000",
            "message": "Need an MVP for my shop.",
            "service": self.service.pk,
            "scope_kind": "ai-automation",
            "scope_size": "Standard",
            "addons": "Copy & content",
            "estimate": "KES 90k – 130k",
            "preferred_slot": "Tue 10:00",
            "source": "quote",
        }
        data.update(overrides)
        return data

    def test_valid_data_creates_enquiry(self):
        form = EnquiryForm(data=self.valid_data())
        self.assertTrue(form.is_valid(), form.errors)
        enquiry = form.save()
        self.assertEqual(enquiry.service, self.service)

    def test_message_is_required(self):
        form = EnquiryForm(data=self.valid_data(message=""))
        self.assertFalse(form.is_valid())
        self.assertIn("message", form.errors)

    def test_calculator_fields_are_optional(self):
        form = EnquiryForm(data=self.valid_data(
            service="", scope_kind="", scope_size="", addons="", estimate="", preferred_slot="",
        ))
        self.assertTrue(form.is_valid(), form.errors)

    def test_non_hidden_fields_get_bp_field_class(self):
        form = EnquiryForm()
        self.assertEqual(form.fields["name"].widget.attrs["class"], "bp-field")
        self.assertNotIn("class", form.fields["service"].widget.attrs)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test website.tests.EnquiryFormTests -v 2`
Expected: FAIL — `ImportError: cannot import name 'EnquiryForm'`

- [ ] **Step 3: Add `EnquiryForm`**

In `website/forms.py`, add after the existing `ContactForm` (import `Enquiry` alongside `ContactMessage`):

```python
from .models import ContactMessage, Enquiry


class EnquiryForm(forms.ModelForm):
    """Backs both the full quote flow and the short enquiry form on a service page."""

    class Meta:
        model = Enquiry
        fields = [
            "name",
            "business",
            "email",
            "phone",
            "message",
            "service",
            "scope_kind",
            "scope_size",
            "addons",
            "estimate",
            "preferred_slot",
            "source",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your name"}),
            "business": forms.TextInput(attrs={"placeholder": "Business name"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email"}),
            "phone": forms.TextInput(attrs={"placeholder": "WhatsApp / phone"}),
            "message": forms.Textarea(
                attrs={"placeholder": "What are you trying to fix or launch?"}
            ),
            "service": forms.HiddenInput(),
            "scope_kind": forms.HiddenInput(),
            "scope_size": forms.HiddenInput(),
            "addons": forms.HiddenInput(),
            "estimate": forms.HiddenInput(),
            "preferred_slot": forms.HiddenInput(),
            "source": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.HiddenInput):
                field.widget.attrs.setdefault("class", "bp-field")
        self.fields["message"].label = "What are you trying to fix or launch?"
```

- [ ] **Step 4: Run the tests**

Run: `python manage.py test website.tests.EnquiryFormTests website.tests.ContactFormTests -v 2`
Expected: all PASS — confirms `ContactForm` is untouched.

- [ ] **Step 5: Commit**

```bash
git add website/forms.py website/tests.py
git commit -m "Add EnquiryForm for the quote flow"
```

---

## Task 4: `Enquiry` admin registration

**Files:**
- Modify: `website/admin.py`
- Test: `website/tests.py`

**Interfaces:**
- Consumes: `Enquiry` model (Task 1).

- [ ] **Step 1: Write the failing test**

Add to `website/tests.py`:

```python
from django.contrib.auth import get_user_model
```

```python
class EnquiryAdminTests(TestCase):
    def test_enquiry_admin_changelist_loads(self):
        User = get_user_model()
        User.objects.create_superuser("admin", "admin@example.com", "password123")
        self.client.login(username="admin", password="password123")
        response = self.client.get(reverse("admin:website_enquiry_changelist"))
        self.assertEqual(response.status_code, 200)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test website.tests.EnquiryAdminTests -v 2`
Expected: FAIL — `NoReverseMatch` (`Enquiry` not registered).

- [ ] **Step 3: Register `Enquiry`**

In `website/admin.py`, add `Enquiry` to the model import and register it:

```python
from .models import Blog, Category, ContactMessage, Enquiry, Project, Service
```

```python
@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "service", "estimate", "source", "created_at", "handled")
    list_filter = ("handled", "source", "created_at")
    search_fields = ("name", "email", "business", "message")
    readonly_fields = (
        "name", "business", "email", "phone", "message", "service",
        "scope_kind", "scope_size", "addons", "estimate", "preferred_slot",
        "source", "created_at",
    )
```

- [ ] **Step 4: Run the test**

Run: `python manage.py test website.tests.EnquiryAdminTests -v 2`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add website/admin.py website/tests.py
git commit -m "Register Enquiry in the admin"
```

---

## Task 5: Quote calculator context helper + `QuoteView` + URL

**Files:**
- Modify: `website/views.py`, `website/urls.py`
- Test: `website/tests.py`

**Interfaces:**
- Consumes: `EnquiryForm` (Task 3), `pricing.SCOPE_SIZES`/`QUOTE_ADDONS`/`upcoming_slots()` (existing `website/pricing.py`), `Service`/`Enquiry` models.
- Produces: `quote_calculator_context()` function (returns `{"quote_services": [...], "scope_sizes": [...], "quote_addons": [...]}`), `QuoteView` class, URL name `website:quote` at `/quote/`. Later tasks call `quote_calculator_context()` from `HomeView`/`ServiceView` and render `{% include 'partials/quote-calculator.html' %}` with that context.

- [ ] **Step 1: Write the failing tests**

Add to `website/tests.py`:

```python
from django.core.cache import cache
from .models import Blog, Category, ContactMessage, Enquiry, Project, Service
```

(`cache` and `Enquiry` may already be imported from earlier tasks — add only what's missing.)

```python
@override_settings(
    CONTACT_EMAIL="info@bakpagelabs.com",
    DEFAULT_FROM_EMAIL="website@bakpagelabs.com",
    CONTACT_RATE_LIMIT=5,
    STORAGES=TEST_STORAGES,
)
class QuoteViewTests(TestCase):
    url = reverse("website:quote")
    ajax = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}

    @classmethod
    def setUpTestData(cls):
        cls.service = Service.objects.create(name="AI & automation", slug="ai-automation", price_from=85)

    def setUp(self):
        cache.clear()

    def data(self, **overrides):
        base = {
            "name": "Jane Wanjiku",
            "business": "Jane's Shop",
            "email": "jane@example.com",
            "phone": "0700000000",
            "message": "Need an MVP for my shop.",
            "service": self.service.pk,
            "scope_kind": "ai-automation",
            "scope_size": "Standard",
            "addons": "Copy & content",
            "estimate": "KES 90k – 130k",
            "preferred_slot": "Tue 10:00",
            "source": "quote",
        }
        base.update(overrides)
        return base

    def test_get_renders_calculator_context(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ai-automation")

    def test_get_with_service_query_param_preselects_it(self):
        response = self.client.get(self.url, {"service": "ai-automation"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-bp-preselect="ai-automation"')

    def test_ajax_submit_saves_and_emails(self):
        response = self.client.post(self.url, self.data(), **self.ajax)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertEqual(Enquiry.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["info@bakpagelabs.com"])

    def test_calculator_fields_optional_when_js_did_not_run(self):
        response = self.client.post(
            self.url,
            self.data(service="", scope_kind="", scope_size="", addons="", estimate="", preferred_slot=""),
            **self.ajax,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertEqual(Enquiry.objects.count(), 1)

    def test_invalid_submission_returns_errors(self):
        response = self.client.post(self.url, self.data(email="not-an-email"), **self.ajax)
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json()["errors"])
        self.assertEqual(Enquiry.objects.count(), 0)

    def test_rate_limited_per_ip(self):
        for _ in range(5):
            self.assertEqual(self.client.post(self.url, self.data(), **self.ajax).status_code, 200)
        response = self.client.post(self.url, self.data(), **self.ajax)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(Enquiry.objects.count(), 5)

    def test_csrf_required(self):
        client = self.client_class(enforce_csrf_checks=True)
        self.assertEqual(client.post(self.url, self.data()).status_code, 403)

    def test_non_ajax_submit_renders_confirmation(self):
        response = self.client.post(self.url, self.data())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "we&#x27;ve got it")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test website.tests.QuoteViewTests -v 2`
Expected: FAIL — `NoReverseMatch: Reverse for 'quote' not found`

- [ ] **Step 3: Write `quote_calculator_context()` and `QuoteView`**

In `website/views.py`, update imports and add the helper + view (the `templates/quote.html` it renders is written in Task 17 — until then this task's tests that hit `render()` will fail with `TemplateDoesNotExist`, which is expected and resolved by Task 17's own test run):

```python
from . import pricing
from .forms import ContactForm, EnquiryForm
from .models import Blog, Project, Service
```

```python
def quote_calculator_context():
    """Context shared by every template that includes quote-calculator.html."""
    quote_services = [
        {
            "slug": service.slug,
            "label": service.short_name or service.name,
            "price_from": service.price_from,
            "addon_factor": service.addon_factor,
            "is_retainer": service.is_retainer,
        }
        for service in Service.objects.all()
    ]
    return {
        "quote_services": quote_services,
        "scope_sizes": pricing.SCOPE_SIZES,
        "quote_addons": pricing.QUOTE_ADDONS,
    }


class QuoteView(View):
    """Render the quote calculator page and handle its enquiry submission."""

    success_message = "Thanks — we've got it. We'll call you at your preferred slot to confirm scope."
    error_message = "Please check the highlighted fields and try again."
    throttled_message = "You've sent several enquiries already. Please try again later."

    def get(self, request):
        initial = {"source": "quote"}
        preselect = None
        slug = request.GET.get("service")
        if slug:
            service = Service.objects.filter(slug=slug).first()
            if service:
                initial["service"] = service.pk
                preselect = service.slug
        form = EnquiryForm(initial=initial)
        context = self.build_context(form)
        context["preselect"] = preselect
        context["slots"] = pricing.upcoming_slots()
        return render(request, "quote.html", context)

    def post(self, request):
        form = EnquiryForm(request.POST)
        if not form.is_valid():
            if self.is_ajax(request):
                return JsonResponse(
                    {"ok": False, "message": self.error_message, "errors": form.errors},
                    status=400,
                )
            context = self.build_context(form)
            context["slots"] = pricing.upcoming_slots()
            return render(request, "quote.html", context, status=400)

        ip = request.META.get("REMOTE_ADDR")
        if self.is_throttled(ip):
            if self.is_ajax(request):
                return JsonResponse({"ok": False, "message": self.throttled_message}, status=429)
            context = self.build_context(EnquiryForm())
            context["slots"] = pricing.upcoming_slots()
            return render(request, "quote.html", context, status=429)

        enquiry = form.save()

        try:
            self.send_notification(enquiry)
        except Exception:
            logger.exception("Could not send quote notification email for enquiry %s", enquiry.pk)

        if self.is_ajax(request):
            return JsonResponse({"ok": True, "message": self.success_message})

        context = self.build_context(EnquiryForm())
        context["slots"] = pricing.upcoming_slots()
        context["confirmed"] = True
        return render(request, "quote.html", context)

    def build_context(self, form):
        context = quote_calculator_context()
        context["form"] = form
        return context

    def is_throttled(self, ip):
        key = f"quote-form:{ip}"
        count = cache.get(key, 0)
        if count >= settings.CONTACT_RATE_LIMIT:
            return True
        cache.set(key, count + 1, 60 * 60)
        return False

    def is_ajax(self, request):
        return request.headers.get("x-requested-with") == "XMLHttpRequest"

    def send_notification(self, enquiry):
        lines = [
            "New enquiry from the quote flow",
            "",
            f"Name: {enquiry.name}",
            f"Business: {enquiry.business}",
            f"Email: {enquiry.email}",
            f"Phone: {enquiry.phone}",
            f"Service: {enquiry.service or enquiry.scope_kind}",
            f"Scope: {enquiry.scope_size} {enquiry.addons}".strip(),
            f"Estimate: {enquiry.estimate}",
            f"Preferred slot: {enquiry.preferred_slot}",
            "",
            enquiry.message,
        ]
        EmailMessage(
            subject=f"Website quote enquiry from {enquiry.name or enquiry.email}",
            body="\n".join(lines),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.CONTACT_EMAIL],
            reply_to=[enquiry.email] if enquiry.email else None,
        ).send()
```

Update `HomeView.get` to include the calculator context:

```python
class HomeView(View):
    def get(self, request):
        services = Service.objects.all()
        projects = Project.objects.all()
        blogs = Blog.objects.all()
        template_name = "home.html"
        context = {'services': services, 'projects': projects, 'blogs': blogs}
        context.update(quote_calculator_context())
        return render(request, template_name, context)
```

Update `ServiceView.get_context_data`:

```python
class ServiceView(DetailView):
    model = Service
    template_name = "service-single.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service_list'] = Service.objects.all()
        context.update(quote_calculator_context())
        return context
```

- [ ] **Step 4: Add the URL**

In `website/urls.py`:

```python
from .views import (
    AboutView,
    BlogDetailView,
    BlogView,
    ContactView,
    HomeView,
    ProjectDetailView,
    ProjectListView,
    QuoteView,
    ServiceListView,
    ServiceView,
)
```

```python
    path("quote/", QuoteView.as_view(), name="quote"),
```

(add this line inside `urlpatterns`, e.g. right after the `contact/` path).

- [ ] **Step 5: Run the tests**

Run: `python manage.py test website.tests.QuoteViewTests -v 2`
Expected: FAIL only on the tests that `render()` (`TemplateDoesNotExist: quote.html`) — this is expected until Task 17. Tests that don't reach `render()` on success (none currently — all paths render `quote.html`) will also fail for the same reason. This is acceptable at this point in the plan; re-run this exact command after Task 17 and expect full PASS.

Run: `python manage.py test website.tests.ContactFormTests website.tests.PageTests -v 2`
Expected: PASS — confirms nothing existing broke.

- [ ] **Step 6: Commit**

```bash
git add website/views.py website/urls.py website/tests.py
git commit -m "Add QuoteView, quote URL, and calculator context helper"
```

---

## Task 6: Shared partials — messages, header, mobile nav

**Files:**
- Create: `templates/partials/header.html` (overwrite existing), `templates/partials/mobile-nav.html`
- Modify: `templates/partials/messages.html`
- Test: `website/tests.py`

**Interfaces:**
- Consumes: URL names `website:home/about/service/project/blog/quote`.
- Produces: partials later included from `base.html` (Task 9).

- [ ] **Step 1: Write the failing test**

Add to `website/tests.py`, inside `PageTests`:

```python
    def test_nav_links_to_quote_page(self):
        response = self.client.get(reverse("website:home"))
        self.assertContains(response, reverse("website:quote"))
        self.assertContains(response, "Get a quote")
```

(This will only pass once `base.html`, in Task 9, actually includes the header — until then it's expected to fail. Write it now so Task 9 has it ready.)

- [ ] **Step 2: Write the partials**

Replace `templates/partials/messages.html`:

```html
{% if messages %}
<div class="bp-messages">
  <div class="bp-container">
    {% for message in messages %}
    <p>{{ message }}</p>
    {% endfor %}
  </div>
</div>
{% endif %}
```

Replace `templates/partials/header.html`:

```html
{% load static %}
<header class="bp-header">
  <div class="bp-container bp-header__inner">
    <a class="bp-logo" href="{% url 'website:home' %}">
      <img src="{% static 'assets/logo.png' %}" alt="BakPage Labs">
    </a>
    <nav class="bp-nav">
      <a href="{% url 'website:home' %}"{% if request.resolver_match.url_name == 'home' %} class="is-active"{% endif %}>Home</a>
      <a href="{% url 'website:about' %}"{% if request.resolver_match.url_name == 'about' %} class="is-active"{% endif %}>About</a>
      <a href="{% url 'website:service' %}"{% if request.resolver_match.url_name == 'service' or request.resolver_match.url_name == 'service_detail' %} class="is-active"{% endif %}>Services</a>
      <a href="{% url 'website:project' %}"{% if request.resolver_match.url_name == 'project' or request.resolver_match.url_name == 'project_detail' %} class="is-active"{% endif %}>Work</a>
      <a href="{% url 'website:blog' %}"{% if request.resolver_match.url_name == 'blog' or request.resolver_match.url_name == 'blog_detail' %} class="is-active"{% endif %}>Blog</a>
      <a href="#contact">Contact</a>
      <a href="{% url 'website:quote' %}" class="bp-btn bp-btn--primary bp-btn--small">Get a quote</a>
    </nav>
    <button type="button" class="bp-burger" data-bp-burger aria-label="Menu" aria-expanded="false" aria-controls="mobile-nav">
      <span></span>
    </button>
  </div>
</header>
```

Create `templates/partials/mobile-nav.html`:

```html
<nav class="bp-mobile-nav" id="mobile-nav" data-bp-mobile-nav>
  <div class="bp-container">
    <a href="{% url 'website:home' %}">Home</a>
    <a href="{% url 'website:about' %}">About</a>
    <a href="{% url 'website:service' %}">Services</a>
    <a href="{% url 'website:project' %}">Work</a>
    <a href="{% url 'website:blog' %}">Blog</a>
    <a href="#contact">Contact</a>
    <a href="{% url 'website:quote' %}">Get a quote</a>
  </div>
</nav>
```

- [ ] **Step 3: Run the test**

Run: `python manage.py test website.tests.PageTests.test_nav_links_to_quote_page -v 2`
Expected: FAIL — `base.html` doesn't include the header yet (Task 9). This is expected; re-run after Task 9.

- [ ] **Step 4: Commit**

```bash
git add templates/partials/header.html templates/partials/mobile-nav.html templates/partials/messages.html website/tests.py
git commit -m "Rebuild header, mobile nav and messages partials in the new design"
```

---

## Task 7: Footer partial with inline contact form, and CTA bar

**Files:**
- Create: `templates/partials/cta-bar.html`
- Modify: `templates/partials/footer.html` (overwrite existing), `static/assets/js/redesign.js`, `static/assets/css/redesign.css`
- Test: `website/tests.py`

**Interfaces:**
- Consumes: `website:contact` URL, `ContactForm` (unchanged).
- Produces: the `#pr__contact__form` DOM id the existing `ContactFormTests.test_form_is_on_every_page_once` asserts on, an `#contact` anchor target for the header/mobile-nav "Contact" links, `[data-bp-contact-form]` hook for the new vanilla AJAX handler.

- [ ] **Step 1: Confirm the existing test this task must keep passing**

`website/tests.py` already has:

```python
    def test_form_is_on_every_page_once(self):
        response = self.client.get(reverse("website:home"))
        self.assertContains(response, 'id="pr__contact__form"', count=1)
        self.assertContains(response, f'action="{self.url}"')
        self.assertContains(response, "csrfmiddlewaretoken")
```

No new test is needed for this task — the goal is that this **existing** test keeps passing once the modal becomes an inline panel. Run it now to see it currently pass against the old markup:

Run: `python manage.py test website.tests.ContactFormTests.test_form_is_on_every_page_once -v 2`
Expected: PASS (against the current, unmodified footer/base templates).

- [ ] **Step 2: Replace `templates/partials/footer.html`**

```html
{% load static %}
<footer class="bp-footer-wrap" id="contact">
  <section class="bp-section bp-container">
    <div class="bp-heading-row">
      <div>
        <span class="bp-rule"></span>
        <h2 class="bp-h2">Let's talk.</h2>
      </div>
    </div>
    <div id="pr__contact__form" class="bp-enquiry-card" style="max-width: 560px;">
      <div class="bp-enquiry-card__offset"></div>
      <div class="bp-enquiry-card__inner">
        <form class="pr__form" action="{% url 'website:contact' %}" method="post" data-bp-contact-form>
          {% csrf_token %}
          <input class="bp-field" id="contact-name" name="name" type="text" maxlength="100" placeholder="Your name" required>
          <input class="bp-field" id="contact-email" name="email" type="email" maxlength="254" placeholder="Your email" required>
          <textarea class="bp-field" id="contact-message" name="message" maxlength="5000" placeholder="What are you trying to fix or launch?" required></textarea>
          {# Honeypot: leave empty. Hidden from people, often filled in by bots. #}
          <div style="position: absolute; left: -10000px;" aria-hidden="true">
            <label for="contact-website">Website</label>
            <input id="contact-website" name="website" type="text" tabindex="-1" autocomplete="off">
          </div>
          <div class="pr__contact__status" role="status" aria-live="polite"></div>
          <button class="bp-btn bp-btn--primary bp-btn--block" type="submit">Send message</button>
        </form>
      </div>
    </div>
  </section>
  <div class="bp-footer">
    <div class="bp-footer__contacts">
      <a href="tel:+25477681091">+254 777 681 091</a>
      <a href="mailto:info@bakpagelabs.com">info@bakpagelabs.com</a>
    </div>
    <div class="bp-footer__social">
      <a href="#" aria-label="Facebook">Facebook</a>
      <a href="#" aria-label="Twitter">Twitter</a>
      <a href="#" aria-label="Instagram">Instagram</a>
    </div>
    <p class="bp-footer__copy">© {% now "Y" %} BakPage Labs. All rights reserved.</p>
  </div>
</footer>
```

- [ ] **Step 3: Create `templates/partials/cta-bar.html`**

```html
<div class="bp-ctabar" data-bp-ctabar>
  <div class="bp-container bp-ctabar__inner">
    <p class="bp-ctabar__line">Have a project in mind?</p>
    <a href="#contact" class="bp-btn bp-btn--ghost bp-btn--small">Contact us</a>
    <a href="{% url 'website:quote' %}" class="bp-btn bp-btn--primary">Get a quote</a>
  </div>
</div>
```

- [ ] **Step 4: Add the vanilla AJAX handler to `static/assets/js/redesign.js`**

`main.js` (which used to drive this form's AJAX submit) is being removed in Task 9, so `redesign.js` needs to take over. Add this new numbered section right before the final `function init() {` block, and add a call to it inside `init()`:

```javascript
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
```

Update `init()` at the bottom of the file:

```javascript
	function init() {
		initNav();
		initTabs();
		initCalculators();
		initSteps();
		initContactForm();
	}
```

- [ ] **Step 5: Add supporting CSS**

Append to `static/assets/css/redesign.css` (after section 12, before section 13's responsive block — or simply at the end of the file, since cascade order doesn't matter for this rule):

```css
.pr__contact__status {
	margin-top: 14px;
	font-size: 14px;
	color: var(--bp-text);
}

.pr__contact__status.bp-form-status--error {
	color: var(--bp-red);
}
```

- [ ] **Step 6: Run the test**

Run: `python manage.py test website.tests.ContactFormTests.test_form_is_on_every_page_once -v 2`
Expected: PASS — `id="pr__contact__form"` still appears exactly once, `action`/`csrfmiddlewaretoken` unchanged.

- [ ] **Step 7: Commit**

```bash
git add templates/partials/footer.html templates/partials/cta-bar.html static/assets/js/redesign.js static/assets/css/redesign.css
git commit -m "Rebuild footer with an inline contact panel, add CTA bar"
```

---

## Task 8: Fix the quote calculator's hidden-input wiring

**Files:**
- Modify: `templates/partials/quote-calculator.html`

**Interfaces:**
- Consumes: `redesign.js`'s `initCalculators()`, which looks for `[data-bp-input-kind]`, `[data-bp-input-size]`, `[data-bp-input-addons]`, `[data-bp-input-estimate]` inside `[data-bp-calc]`.
- Produces: hidden `<input>` elements with `name` attributes matching `EnquiryForm`'s hidden fields (`scope_kind`, `scope_size`, `addons`, `estimate`), so that when this partial is embedded inside the quote page's `<form>` (Task 17), a calculator selection actually reaches the submitted `Enquiry`. On the home/service pages, where the partial is *not* inside a `<form>` (it links out to `/quote/` instead), these inputs are simply inert — no naming collision risk since they don't belong to any form there.

This partial currently has no test exercising it directly (it's exercised indirectly once Tasks 12–14 and 17 render it). No test is added in this task; Task 17's `QuoteViewTests` (already written in Task 5) exercises the wiring once the quote page exists.

- [ ] **Step 1: Add the missing hidden inputs**

Replace `templates/partials/quote-calculator.html` with:

```html
{% load l10n %}
{% localize off %}
<div class="bp-calc" data-bp-calc{% if preselect %} data-bp-preselect="{{ preselect }}"{% endif %}>
  <div class="bp-calc__picker">
    <span class="bp-label">1 · What are we building?</span>
    <div class="bp-chip-row">
      {% for service in quote_services %}
      <button type="button" class="bp-chip" data-bp-kind data-value="{{ service.slug }}" data-label="{{ service.label }}"
        data-base="{{ service.price_from }}" data-factor="{{ service.addon_factor }}"
        data-retainer="{{ service.is_retainer|yesno:'true,false' }}" aria-pressed="false">{{ service.label }}</button>
      {% endfor %}
    </div>
    <span class="bp-label">2 · How big is it?</span>
    <div class="bp-chip-row">
      {% for size in scope_sizes %}
      <button type="button" class="bp-chip" data-bp-size data-label="{{ size.label }}" data-mult="{{ size.mult }}"
        data-weeks="{{ size.weeks }}" aria-pressed="false">{{ size.label }} · {{ size.weeks }}</button>
      {% endfor %}
    </div>
    <span class="bp-label">3 · Add-ons</span>
    <div class="bp-chip-row">
      {% for addon in quote_addons %}
      <button type="button" class="bp-chip" data-bp-addon data-label="{{ addon.label }}" data-add="{{ addon.add }}"
        {% if addon.default %}data-bp-default{% endif %} aria-pressed="false">{{ addon.label }}</button>
      {% endfor %}
    </div>
  </div>
  <div class="bp-calc__result">
    <span class="bp-label">Indicative range</span>
    <div class="bp-calc__figure" data-bp-estimate>On enquiry</div>
    <div class="bp-calc__timeline" data-bp-timeline></div>
    <div class="bp-calc__divider"></div>
    <p class="bp-calc__note" data-bp-note></p>
    <input type="hidden" name="scope_kind" data-bp-input-kind>
    <input type="hidden" name="scope_size" data-bp-input-size>
    <input type="hidden" name="addons" data-bp-input-addons>
    <input type="hidden" name="estimate" data-bp-input-estimate>
    {% if not is_embedded_in_quote_form %}
    <a href="{% url 'website:quote' %}{% if preselect %}?service={{ preselect }}{% endif %}" class="bp-btn bp-btn--primary bp-btn--block">Lock this scope in a call</a>
    {% endif %}
    <p class="bp-fineprint">Ranges are indicative and can be phased or paid monthly. Final quote follows a 30-minute
      scoping call — free, no deck required.</p>
  </div>
</div>
{% endlocalize %}
```

(`is_embedded_in_quote_form` is passed as `True` from `templates/quote.html` in Task 17, since that page already has its own submit button further down the form — everywhere else, the CTA link is shown.)

- [ ] **Step 2: Commit**

```bash
git add templates/partials/quote-calculator.html
git commit -m "Wire the quote calculator's hidden inputs to EnquiryForm field names"
```

---

## Task 9: `base.html` shell assembly

**Files:**
- Modify: `templates/base.html`
- Test: `website/tests.py` (run existing suite; add one new assertion)

**Interfaces:**
- Consumes: `partials/messages.html`, `partials/header.html`, `partials/mobile-nav.html`, `partials/footer.html`, `partials/cta-bar.html` (Tasks 6–7), `static/assets/css/redesign.css`, `static/assets/js/redesign.js`.
- Produces: single `<body class="bp bp-body-pad">` for the whole site; `{% block title %}`, `{% block content %}`, `{% block cta_bar %}`, `{% block hero_scene_script %}` for child templates to use.

- [ ] **Step 1: Write the failing test**

This task's test is the whole existing suite, plus the nav-link test from Task 6. Run both now to confirm they currently fail against the old `base.html`:

Run: `python manage.py test website.tests.PageTests.test_nav_links_to_quote_page -v 2`
Expected: FAIL (header not yet included from `base.html`).

- [ ] **Step 2: Replace `templates/base.html`**

```html
{% load static %}
<!DOCTYPE html>
<html lang="en">

<head>
  <title>{% block title %}BakPage Labs{% endblock %}</title>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="msapplication-TileColor" content="#E9204F">
  <meta name="theme-color" content="#0c0c0d">
  <link rel="apple-touch-icon" sizes="180x180" href="{% static 'assets/images/apple-touch-icon.png' %}">
  <link rel="icon" type="image/png" sizes="32x32" href="{% static 'assets/images/favicon-32x32.png' %}">
  <link rel="icon" type="image/png" sizes="16x16" href="{% static 'assets/images/favicon-16x16.png' %}">
  <link rel="icon" href="{% static 'favicon.ico' %}" sizes="any">
  <script data-ad-client="ca-pub-8128509305831596" async
    src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
  <link rel="stylesheet" href="{% static 'assets/css/fonts.css' %}">
  <link rel="stylesheet" href="{% static 'assets/css/redesign.css' %}">
</head>

<body class="bp bp-body-pad">
  {% include 'partials/messages.html' %}
  {% include 'partials/header.html' %}
  {% include 'partials/mobile-nav.html' %}

  {% block content %}
  {% endblock %}

  {% include 'partials/footer.html' %}
  {% block cta_bar %}{% include 'partials/cta-bar.html' %}{% endblock %}

  <script src="{% static 'assets/js/redesign.js' %}"></script>
  <script src="https://cdn.jsdelivr.net/npm/lenis@1.1.13/dist/lenis.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.12.7/dist/gsap.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.12.7/dist/ScrollTrigger.min.js"></script>
  <script src="{% static 'assets/js/motion.js' %}"></script>
  {% block hero_scene_script %}{% endblock %}
</body>

</html>
```

This drops `normalize.min.css`, `pr.animation.css`, `owl.carousel.min.css`, `uikit.min.css`, `pixeicons.css`, `style.css`, `jquery.min.js`, `anime.min.js`, `pr.animation.js`, `uikit.min.js`, `owl.carousel.min.js`, `validate.js`, and `main.js` entirely.

- [ ] **Step 3: Run the tests**

Run: `python manage.py test website.tests.PageTests.test_nav_links_to_quote_page -v 2`
Expected: still FAIL right now, because every page template (`home.html` etc.) still has its own old `{% include 'partials/header.html' %}` inside its content block, plus its own `<body>`/`<div class="pr__wrapper">` wrappers, so the page would currently render the header *twice* with broken nesting. **Do not treat this as a regression to fix here** — Tasks 12–17 rewrite every page template's content block to drop that duplication. Confirm instead that the app still boots:

Run: `python manage.py check`
Expected: `System check identified no issues`

Run: `python manage.py test website.tests.ContactFormTests -v 2`
Expected: some of these will also fail until the page templates are rewritten (duplicate header markup can break the single-occurrence assertions). This is expected and resolved by the end of Task 17 — re-run the full suite there.

- [ ] **Step 4: Commit**

```bash
git add templates/base.html
git commit -m "Rebuild base.html shell on the new design system"
```

---

## Task 10: Motion layer — Lenis smooth scroll + GSAP reveals

**Files:**
- Create: `static/assets/js/motion.js`

**Interfaces:**
- Consumes: `window.Lenis`, `window.gsap`, `window.ScrollTrigger` (CDN, loaded by `base.html` in Task 9); reads `data-bp-count` attributes for stat counters (used by `home.html` in Task 12).
- Produces: automatic scroll-reveal on `.bp-section, .bp-offset, .bp-work-card, .bp-tile, .bp-studio-card, .bp-testimonial`; count-up animation on any `[data-bp-count]` element. No public API — self-initializing like `redesign.js`.

No Django test applies to this file (it's pure client-side behavior and this repo has no JS test runner — see Global Constraints). Verification is by code review plus the manual QA pass in Task 18.

- [ ] **Step 1: Write `static/assets/js/motion.js`**

```javascript
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
```

- [ ] **Step 2: Manual verification**

Run the dev server (`python manage.py runserver`), open the home page in a browser, and confirm: (a) sections fade/rise into view on scroll, (b) scrolling feels smooth/inertial, (c) with the OS "reduce motion" setting on, everything is instantly visible with no animation.

- [ ] **Step 3: Commit**

```bash
git add static/assets/js/motion.js
git commit -m "Add Lenis + GSAP motion layer with reduced-motion fallback"
```

---

## Task 11: Three.js hero background scene

**Files:**
- Create: `static/assets/js/hero-scene.js`
- Modify: `static/assets/css/redesign.css`

**Interfaces:**
- Consumes: `window.THREE` (CDN, loaded only where this script is included — `home.html`, Task 12), a `[data-bp-hero-scene]` hero element containing a `[data-bp-scene-canvas]` `<canvas>`.
- Produces: no public API — self-initializing.

No Django test applies (client-side WebGL behavior). Verified manually in Task 18's QA pass.

- [ ] **Step 1: Add hero canvas CSS**

Append to `static/assets/css/redesign.css`:

```css
.bp-hero__scene {
	position: absolute;
	inset: 0;
	width: 100%;
	height: 100%;
}
```

- [ ] **Step 2: Write `static/assets/js/hero-scene.js`**

```javascript
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
			} else if (hero.getBoundingClientRect().top < window.innerHeight) {
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
```

- [ ] **Step 3: Manual verification**

After Task 12 wires this into `home.html`, load the home page and confirm: (a) a faint drifting red/white particle field appears behind the hero and reacts gently to mouse movement, (b) it disappears once scrolled past, (c) with "reduce motion" on, or in a browser with WebGL disabled, the hero shows only the static image + gradient with no console errors.

- [ ] **Step 4: Commit**

```bash
git add static/assets/js/hero-scene.js static/assets/css/redesign.css
git commit -m "Add scoped Three.js hero background scene"
```

---

## Task 12: Home page template

**Files:**
- Modify: `templates/home.html` (overwrite existing)
- Test: `website/tests.py`

**Interfaces:**
- Consumes: `HomeView`'s context (`services`, `projects`, `blogs`, `quote_services`, `scope_sizes`, `quote_addons` — Task 5), `partials/quote-calculator.html` (Task 8), `hero-scene.js` (Task 11).

- [ ] **Step 1: Write the failing tests**

Add to `website/tests.py`, inside `PageTests`:

```python
    def test_home_page_renders_services_and_work(self):
        response = self.client.get(reverse("website:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project.name)
        self.assertContains(response, "data-bp-calc")

    def test_home_page_loads_hero_scene_script_once(self):
        response = self.client.get(reverse("website:home"))
        self.assertContains(response, "hero-scene.js", count=1)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test website.tests.PageTests.test_home_page_renders_services_and_work website.tests.PageTests.test_home_page_loads_hero_scene_script_once -v 2`
Expected: FAIL against the current `home.html`.

- [ ] **Step 3: Replace `templates/home.html`**

```html
{% extends 'base.html' %}
{% load static %}
{% block title %}BakPage Labs — Technology partner for growing businesses{% endblock %}

{% block hero_scene_script %}
<script src="https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.min.js"></script>
<script src="{% static 'assets/js/hero-scene.js' %}"></script>
{% endblock %}

{% block content %}
<section class="bp-hero" data-bp-hero-scene>
  <div class="bp-hero__bg" style="background-image: url('{% static 'assets/images/hero_02.jpg' %}');"></div>
  <div class="bp-hero__scrim"></div>
  <canvas class="bp-hero__scene" data-bp-scene-canvas aria-hidden="true"></canvas>
  <div class="bp-container bp-hero__inner">
    <span class="bp-label bp-label--red">Technology partner for growing businesses</span>
    <h1 class="bp-h1">We build the software your business runs on.</h1>
    <div class="bp-hero__actions">
      <a href="#services" class="bp-btn bp-btn--primary">See what we build</a>
      <a href="{% url 'website:quote' %}" class="bp-btn bp-btn--ghost">Get a quote</a>
    </div>
  </div>
  <div class="bp-container">
    <div class="bp-stats">
      <div>
        <div class="bp-num">2021</div>
        <div class="bp-label">Founded</div>
      </div>
      {# TODO: replace with real figures once available #}
      <div>
        <div class="bp-num"><span data-bp-count="30">0</span>+</div>
        <div class="bp-label">Projects shipped</div>
      </div>
      <div>
        <div class="bp-num"><span data-bp-count="20">0</span>+</div>
        <div class="bp-label">Clients served</div>
      </div>
      <div>
        <div class="bp-num"><span data-bp-count="6">0</span></div>
        <div class="bp-label">Core services</div>
      </div>
    </div>
  </div>
</section>

<section class="bp-section bp-container">
  <div class="bp-grid bp-grid--3">
    <div class="bp-feature">
      <div class="bp-feature-icon bp-feature-icon--red"></div>
      <h3>AI-first approach</h3>
      <p>We integrate AI into real business workflows — not as a gimmick, but as infrastructure that saves time and money.</p>
    </div>
    <div class="bp-feature">
      <div class="bp-feature-icon bp-feature-icon--red"></div>
      <h3>Ship fast, iterate</h3>
      <p>Working software every two weeks. No six-month vanishing acts — you see progress, give feedback, and stay in control.</p>
    </div>
    <div class="bp-feature">
      <div class="bp-feature-icon bp-feature-icon--red"></div>
      <h3>Built for East Africa</h3>
      <p>M-Pesa integration, offline-capable systems, and interfaces designed for real network conditions and real users.</p>
    </div>
  </div>
</section>

<section class="bp-section bp-container" id="services">
  <div class="bp-heading-row">
    <div>
      <span class="bp-rule"></span>
      <h2 class="bp-h2">What we build.</h2>
    </div>
    <a href="{% url 'website:service' %}" class="bp-link">All services</a>
  </div>
  {% if services %}
  <div class="bp-grid bp-grid--3">
    {% for service in services %}
    <a href="{{ service.get_absolute_url }}" class="bp-offset">
      <div class="bp-offset__inner bp-service-card">
        <div class="bp-service-card__top">
          <span class="bp-service-card__num">{{ forloop.counter|stringformat:"02d" }}</span>
          {% if service.price_from %}
          <span class="bp-service-card__price">From KES {{ service.price_from }}k</span>
          {% endif %}
        </div>
        <h3>{{ service.short_name|default:service.name }}</h3>
        <p>{{ service.tagline|default:service.summary|default:service.description|truncatechars:120 }}</p>
        <span class="bp-service-card__more">Learn more →</span>
      </div>
    </a>
    {% endfor %}
  </div>
  {% endif %}
</section>

<section class="bp-section bp-container" id="work">
  <div class="bp-heading-row">
    <div>
      <span class="bp-rule"></span>
      <h2 class="bp-h2">Recent work.</h2>
    </div>
    <a href="{% url 'website:project' %}" class="bp-link">View all</a>
  </div>
  {% if projects %}
  <div class="bp-grid bp-grid--3">
    {% for project in projects|slice:":6" %}
    <a href="{{ project.get_absolute_url }}" class="bp-tile">
      <div class="bp-work-card__img" style="position: absolute; inset: 0; background-image: url('{{ project.image.url }}');"></div>
      <div class="bp-work-card__scrim"></div>
      <div class="bp-tile__body">
        <div class="bp-work-card__tags">
          {% for tag in project.tags.all %}<span class="bp-tag">{{ tag.name }}</span>{% endfor %}
        </div>
        <h3>{{ project.headline|default:project.name }}</h3>
      </div>
    </a>
    {% endfor %}
  </div>
  {% endif %}
</section>

<section class="bp-section bp-container">
  <div class="bp-testimonial">
    <div class="bp-testimonial__img" style="background-image: url('{% static 'assets/images/brian.jpg' %}');"></div>
    <div class="bp-testimonial__body">
      <p class="bp-testimonial__quote">"We are motivated by the satisfaction of our clients. Put your trust in us and let us share in your growth. BakPage is made up of a team of expert, committed and experienced people with a passion for digital markets. Our goal is to achieve continuous and sustainable growth of our clients."</p>
      <p class="bp-label">Brian Josh — Designer / Developer</p>
    </div>
  </div>
</section>

<section class="bp-section bp-container">
  <div class="bp-heading-row">
    <div>
      <span class="bp-rule"></span>
      <h2 class="bp-h2">Get a ballpark estimate.</h2>
    </div>
  </div>
  {% include 'partials/quote-calculator.html' %}
</section>

{% if blogs %}
<section class="bp-section bp-container">
  <div class="bp-heading-row">
    <div>
      <span class="bp-rule"></span>
      <h2 class="bp-h2">Latest thinking.</h2>
    </div>
    <a href="{% url 'website:blog' %}" class="bp-link">All posts</a>
  </div>
  <div class="bp-grid bp-grid--3">
    {% for blog in blogs|slice:":3" %}
    <a href="{{ blog.get_absolute_url }}" class="bp-studio-card">
      <div class="bp-studio-card__img" style="background-image: url('{{ blog.image.url }}');"></div>
      <div class="bp-studio-card__body">
        <h3>{{ blog.title }}</h3>
        <p>{{ blog.text|truncatechars:120 }}</p>
      </div>
    </a>
    {% endfor %}
  </div>
</section>
{% endif %}
{% endblock %}
```

- [ ] **Step 4: Run the tests**

Run: `python manage.py test website.tests.PageTests -v 2`
Expected: PASS — including `test_home_page_renders_services_and_work`, `test_home_page_loads_hero_scene_script_once`, and (now that the duplicate header is gone from this page) `test_nav_links_to_quote_page` and `test_no_relative_asset_paths` for the home page specifically. (Other pages in that test still fail until Tasks 13–17 land — that's expected; the full suite is green again by the end of Task 17.)

- [ ] **Step 5: Commit**

```bash
git add templates/home.html website/tests.py
git commit -m "Rebuild the home page in the new design"
```

---

## Task 13: Services list + detail templates

**Files:**
- Modify: `templates/service-list.html`, `templates/service-single.html` (overwrite existing)
- Test: `website/tests.py`

**Interfaces:**
- Consumes: `ServiceListView`'s `object_list`, `ServiceView`'s context (`object`, `service_list`, `quote_services`/`scope_sizes`/`quote_addons` — Task 5).

- [ ] **Step 1: Write the failing tests**

Add to `website/tests.py`, inside `PageTests`:

```python
    def test_service_list_shows_accordion(self):
        response = self.client.get(reverse("website:service"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "bp-accordion")

    def test_service_detail_preselects_calculator(self):
        service = Service.objects.first()
        response = self.client.get(service.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'data-bp-preselect="{service.slug}"')
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test website.tests.PageTests.test_service_list_shows_accordion website.tests.PageTests.test_service_detail_preselects_calculator -v 2`
Expected: FAIL against the current templates.

- [ ] **Step 3: Replace `templates/service-list.html`**

```html
{% extends 'base.html' %}
{% block title %}Services — BakPage Labs{% endblock %}
{% block content %}
<section class="bp-hero bp-hero--page">
  <div class="bp-hero__scrim bp-hero__scrim--down"></div>
  <div class="bp-container bp-hero__inner bp-hero__inner--short">
    <span class="bp-label bp-label--red">What we build</span>
    <h1 class="bp-h1">AI-powered software, automation, and tech strategy.</h1>
  </div>
</section>
<section class="bp-section bp-container">
  <div class="bp-accordion">
    {% for service in object_list %}
    <details class="bp-accordion__item"{% if forloop.first %} open{% endif %}>
      <summary class="bp-accordion__summary">
        <span class="bp-accordion__num">{{ forloop.counter|stringformat:"02d" }}</span>
        <span class="bp-accordion__title">
          <b>{{ service.short_name|default:service.name }}</b>
          <span>{{ service.tagline }}</span>
        </span>
        {% if service.price_from %}
        <span class="bp-accordion__price">From KES {{ service.price_from }}k{% if service.is_retainer %} / mo{% endif %}</span>
        {% endif %}
        <span class="bp-accordion__sign"></span>
      </summary>
      <div class="bp-accordion__body">
        <div>
          <p>{{ service.summary|default:service.description|truncatewords:60 }}</p>
          {% if service.highlights %}
          <div class="bp-points">
            {% for line in service.highlights.splitlines %}
            {% if line %}<div class="bp-tag">{{ line }}</div>{% endif %}
            {% endfor %}
          </div>
          {% endif %}
          <a href="{{ service.get_absolute_url }}" class="bp-link">See details</a>
        </div>
        <div class="bp-facts">
          {% if service.timeline %}
          <div class="bp-fact bp-fact--red">
            <span class="bp-label">Timeline</span>
            <div>{{ service.timeline }}</div>
          </div>
          {% endif %}
          {% if service.deliverable %}
          <div class="bp-fact">
            <span class="bp-label">You get</span>
            <div>{{ service.deliverable }}</div>
          </div>
          {% endif %}
        </div>
      </div>
    </details>
    {% endfor %}
  </div>
</section>
{% endblock %}
```

- [ ] **Step 4: Replace `templates/service-single.html`**

```html
{% extends 'base.html' %}
{% block title %}{{ object.name }} — BakPage Labs{% endblock %}
{% block content %}
<section class="bp-hero bp-hero--page">
  <div class="bp-hero__scrim bp-hero__scrim--down"></div>
  <div class="bp-container bp-hero__inner bp-hero__inner--short">
    <span class="bp-label bp-label--red">Services</span>
    <h1 class="bp-h1">{{ object.name }}</h1>
    {% if object.tagline %}<p class="bp-lead bp-measure">{{ object.tagline }}</p>{% endif %}
  </div>
</section>
<section class="bp-section bp-container" style="display: grid; grid-template-columns: 1fr 0.5fr; gap: 64px;">
  <div>
    {% if object.image %}
    <div class="bp-offset--media" style="margin-bottom: 32px;">
      <div class="bp-offset__inner"><img src="{{ object.imageURL }}" alt="{{ object.name }}"></div>
    </div>
    {% endif %}
    <div class="bp-prose">
      {{ object.formatted_markdown|safe }}
    </div>
  </div>
  <aside>
    <div class="bp-panel">
      <span class="bp-label">Other services</span>
      <div style="display: flex; flex-direction: column; gap: 10px; margin-top: 16px;">
        {% for svc in service_list %}
        <a href="{{ svc.get_absolute_url }}" class="bp-link"{% if svc.slug == object.slug %} style="color: var(--bp-red);"{% endif %}>{{ svc.short_name|default:svc.name }}</a>
        {% endfor %}
      </div>
    </div>
    <div class="bp-panel bp-panel--red">
      <span class="bp-label">Get an estimate</span>
      <h3 class="bp-h4" style="margin: 10px 0 20px;">See what {{ object.name|lower }} costs.</h3>
      {% include 'partials/quote-calculator.html' with preselect=object.slug %}
    </div>
  </aside>
</section>
{% endblock %}
```

- [ ] **Step 5: Run the tests**

Run: `python manage.py test website.tests.PageTests -v 2`
Expected: PASS for services-related tests.

- [ ] **Step 6: Commit**

```bash
git add templates/service-list.html templates/service-single.html website/tests.py
git commit -m "Rebuild services list and detail pages in the new design"
```

---

## Task 14: Work/project list + detail templates

**Files:**
- Modify: `templates/project-list.html`, `templates/project-single.html` (overwrite existing)
- Test: `website/tests.py`

**Interfaces:**
- Consumes: `ProjectListView`'s `object_list`, `ProjectDetailView`'s context (`object`, `project_list`).

- [ ] **Step 1: Write the failing tests**

Add to `website/tests.py`, inside `PageTests`:

```python
    def test_project_list_renders(self):
        response = self.client.get(reverse("website:project"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project.name)

    def test_project_detail_degrades_gracefully_without_case_study_fields(self):
        # self.project (from setUpTestData) has no headline/summary/metrics/
        # scope/stack/year set — the case study page must not render empty
        # labels or dashes for them.
        response = self.client.get(self.project.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project.name)  # headline falls back to name
        content = response.content.decode()
        self.assertNotIn("Scope</dt>", content)
        self.assertNotIn("Stack</dt>", content)
        self.assertNotIn("Year</dt>", content)

    def test_project_detail_shows_case_study_fields_when_present(self):
        rich_category = Category.objects.create(name="Fintech")
        rich_project = Project.objects.create(
            name="Rich Co", image="rich.png", description="desc",
            category=rich_category, slug="rich-co",
            headline="Rich Co case study", scope="Platform, brand",
            stack="Django, Postgres", year="2025",
            metrics="3.1×|Case intake per month",
        )
        response = self.client.get(rich_project.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rich Co case study")
        self.assertContains(response, "Platform, brand")
        self.assertContains(response, "3.1×")
        self.assertContains(response, "Case intake per month")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test website.tests.PageTests.test_project_list_renders website.tests.PageTests.test_project_detail_degrades_gracefully_without_case_study_fields website.tests.PageTests.test_project_detail_shows_case_study_fields_when_present -v 2`
Expected: FAIL against the current templates.

- [ ] **Step 3: Replace `templates/project-list.html`**

```html
{% extends 'base.html' %}
{% block title %}Work — BakPage Labs{% endblock %}
{% block content %}
<section class="bp-hero bp-hero--page">
  <div class="bp-hero__scrim bp-hero__scrim--down"></div>
  <div class="bp-container bp-hero__inner bp-hero__inner--short">
    <span class="bp-label bp-label--red">Selected work</span>
    <h1 class="bp-h1">Things we've made.</h1>
  </div>
</section>
<section class="bp-section bp-container">
  <div class="bp-grid bp-grid--3">
    {% for project in object_list %}
    <a href="{{ project.get_absolute_url }}" class="bp-tile">
      <div class="bp-work-card__img" style="position: absolute; inset: 0; background-image: url('{{ project.image.url }}');"></div>
      <div class="bp-work-card__scrim"></div>
      <div class="bp-tile__body">
        <div class="bp-work-card__tags">
          {% if project.category %}<span class="bp-tag bp-tag--red">{{ project.category }}</span>{% endif %}
        </div>
        <h3>{{ project.headline|default:project.name }}</h3>
      </div>
    </a>
    {% endfor %}
  </div>
</section>
{% endblock %}
```

- [ ] **Step 4: Replace `templates/project-single.html`**

```html
{% extends 'base.html' %}
{% block title %}{{ object.name }} — BakPage Labs{% endblock %}
{% block content %}
<section class="bp-hero bp-hero--page">
  <div class="bp-hero__scrim bp-hero__scrim--down"></div>
  <div class="bp-container bp-hero__inner bp-hero__inner--short">
    <span class="bp-label bp-label--red">{{ object.category|default:"Case study" }}</span>
    <h1 class="bp-h1">{{ object.headline|default:object.name }}</h1>
    {% if object.summary %}<p class="bp-lead bp-measure">{{ object.summary }}</p>{% endif %}
  </div>
</section>
<section class="bp-section bp-container bp-case-layout">
  <div class="bp-chapter">
    <div class="bp-prose">
      <p>{{ object.description }}</p>
    </div>
    <div class="bp-offset--media" style="margin-top: 32px;">
      <div class="bp-offset__inner"><img src="{{ object.image.url }}" alt="{{ object.name }}"></div>
    </div>
    {% if object.image1URL or object.image2URL or object.image3URL %}
    <div class="bp-grid bp-grid--3" style="margin-top: 24px;">
      {% if object.image1URL %}<img src="{{ object.image1URL }}" alt="{{ object.name }}" style="border: 1px solid var(--bp-line);">{% endif %}
      {% if object.image2URL %}<img src="{{ object.image2URL }}" alt="{{ object.name }}" style="border: 1px solid var(--bp-line);">{% endif %}
      {% if object.image3URL %}<img src="{{ object.image3URL }}" alt="{{ object.name }}" style="border: 1px solid var(--bp-line);">{% endif %}
    </div>
    {% endif %}
    {% if object.metrics_list %}
    <div class="bp-work-card__metrics" style="margin-top: 32px;">
      {% for value, label in object.metrics_list %}
      <div>
        <div class="bp-num">{{ value }}</div>
        <span class="bp-label">{{ label }}</span>
      </div>
      {% endfor %}
    </div>
    {% endif %}
  </div>
  <aside>
    <div class="bp-panel">
      <span class="bp-label">Project details</span>
      <dl class="bp-deflist" style="margin-top: 20px;">
        {% if object.client %}<div><dt>Client</dt><dd>{{ object.client }}</dd></div>{% endif %}
        {% if object.year %}<div><dt>Year</dt><dd>{{ object.year }}</dd></div>{% endif %}
        {% if object.scope %}<div><dt>Scope</dt><dd>{{ object.scope }}</dd></div>{% endif %}
        {% if object.stack %}<div><dt>Stack</dt><dd>{{ object.stack }}</dd></div>{% endif %}
        {% if object.category %}<div><dt>Category</dt><dd>{{ object.category }}</dd></div>{% endif %}
      </dl>
      {% if object.link %}<a href="{{ object.link }}" class="bp-btn bp-btn--ghost bp-btn--block" style="margin-top: 20px;">Visit site</a>{% endif %}
    </div>
  </aside>
</section>
{% if project_list %}
<section class="bp-section bp-container">
  <div class="bp-heading-row">
    <div><span class="bp-rule"></span><h2 class="bp-h2">Related work.</h2></div>
  </div>
  <div class="bp-grid bp-grid--3">
    {% for related in project_list|slice:":3" %}
    {% if related.slug != object.slug %}
    <a href="{{ related.get_absolute_url }}" class="bp-tile">
      <div class="bp-work-card__img" style="position: absolute; inset: 0; background-image: url('{{ related.image.url }}');"></div>
      <div class="bp-work-card__scrim"></div>
      <div class="bp-tile__body"><h3>{{ related.headline|default:related.name }}</h3></div>
    </a>
    {% endif %}
    {% endfor %}
  </div>
</section>
{% endif %}
{% endblock %}
```

- [ ] **Step 5: Run the tests**

Run: `python manage.py test website.tests.PageTests -v 2`
Expected: PASS for project-related tests, including the two new fallback/degradation tests.

- [ ] **Step 6: Commit**

```bash
git add templates/project-list.html templates/project-single.html website/tests.py
git commit -m "Rebuild work/project list and case-study pages, degrading gracefully when fields are blank"
```

---

## Task 15: About page template

**Files:**
- Modify: `templates/about.html` (overwrite existing)
- Test: `website/tests.py`

- [ ] **Step 1: Write the failing test**

Add to `website/tests.py`, inside `PageTests`:

```python
    def test_about_page_renders(self):
        response = self.client.get(reverse("website:about"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Who we are")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test website.tests.PageTests.test_about_page_renders -v 2`
Expected: FAIL (assertion may pass by coincidence against the old template's own "Who we are" heading — if so, this confirms the string; the real check is Step 4's full-suite run once the template is replaced).

- [ ] **Step 3: Replace `templates/about.html`**

```html
{% extends 'base.html' %}
{% load static %}
{% block title %}About — BakPage Labs{% endblock %}
{% block content %}
<section class="bp-hero bp-hero--page">
  <div class="bp-hero__scrim bp-hero__scrim--down"></div>
  <div class="bp-container bp-hero__inner bp-hero__inner--short">
    <span class="bp-label bp-label--red">About us</span>
    <h1 class="bp-h1">We're more than a digital agency.</h1>
  </div>
</section>
<section class="bp-section bp-container">
  <div class="bp-split">
    <div>
      <span class="bp-rule"></span>
      <h2 class="bp-h2">Who we are.</h2>
    </div>
    <div class="bp-prose">
      <p>Our team of creative and technical professionals have extensive experience developing marketing solutions to help you communicate more effectively with potential customers, current customers and employees. We do this through clear communication and thoughtful technology solutions.</p>
      <p>We can take on 100% of a project or work with your team on specific tasks to get you the results you need.</p>
    </div>
  </div>
</section>
<section class="bp-section bp-container">
  <div class="bp-grid bp-grid--3">
    <div class="bp-studio-card">
      <div class="bp-studio-card__img" style="background-image: url('{% static 'assets/images/about_01.jpg' %}');"></div>
      <div class="bp-studio-card__body">
        <h3>Who we are</h3>
        <p>We are an experienced marketing, communications, graphics design and web development company located in Nairobi, KE with clients across Kenya.</p>
      </div>
    </div>
    <div class="bp-studio-card">
      <div class="bp-studio-card__img" style="background-image: url('{% static 'assets/images/about_02.jpg' %}');"></div>
      <div class="bp-studio-card__body">
        <h3>What we do</h3>
        <p>Our focus is to help you increase brand awareness and make your business more efficient and more profitable, by helping you create your own unique identity.</p>
      </div>
    </div>
    <div class="bp-studio-card">
      <div class="bp-studio-card__img" style="background-image: url('{% static 'assets/images/about_03.jpg' %}');"></div>
      <div class="bp-studio-card__body">
        <h3>Our philosophy</h3>
        <p>Working software over decks. We'd rather ship something you can click through in week two than present a roadmap in month three.</p>
      </div>
    </div>
  </div>
</section>
<section class="bp-section bp-container">
  <div class="bp-heading-row">
    <div><span class="bp-rule"></span><h2 class="bp-h2">Our strategies.</h2></div>
  </div>
  <div class="bp-accordion">
    <details class="bp-accordion__item" open>
      <summary class="bp-accordion__summary">
        <span class="bp-accordion__num">01</span>
        <span class="bp-accordion__title"><b>Development strategy</b></span>
        <span class="bp-accordion__sign"></span>
      </summary>
      <div class="bp-accordion__body" style="grid-template-columns: 1fr;">
        <div class="bp-prose">
          <h3>Do you have clearly defined requirements for your future application?</h3>
          <p>We incorporate both linear and evolutionary development models depending on whether your requirements are going to change in the future.</p>
          <h3>Choose the right technology platform</h3>
          <p>Selecting a technology platform (language, frameworks, patterns, APIs and more) is important, as the difference in development speed can be 2–20×.</p>
          <h3>Apply automation</h3>
          <p>Automation in development, testing and deployment — containerisation, test automation and DevOps.</p>
          <h3>Develop iteratively</h3>
          <p>We start with an MVP or a first basic version, giving you a working solution with must-have functions early, adding more as we go based on user feedback.</p>
        </div>
      </div>
    </details>
    <details class="bp-accordion__item">
      <summary class="bp-accordion__summary">
        <span class="bp-accordion__num">02</span>
        <span class="bp-accordion__title"><b>Design strategy</b></span>
        <span class="bp-accordion__sign"></span>
      </summary>
      <div class="bp-accordion__body" style="grid-template-columns: 1fr;">
        <div class="bp-prose">
          <h3>Create a superb brand identity</h3>
          <p>Our designers put across a brand message that helps develop a great identity — a unique logo, colour and typography that stir the right feelings for your target audience.</p>
          <h3>Fortify your business's position</h3>
          <p>An eye-catching design that involves all the significant information about your business, kept up to date as the business grows.</p>
          <h3>Put your business distant from competitors</h3>
          <p>We draw attention to the salient features of your products or services, with materials grounded in your actual differentiation.</p>
        </div>
      </div>
    </details>
  </div>
</section>
<section class="bp-section bp-container">
  <div class="bp-heading-row">
    <div><span class="bp-rule"></span><h2 class="bp-h2">Core services.</h2></div>
  </div>
  <div class="bp-grid bp-grid--3">
    {% for service in services %}
    <a href="{{ service.get_absolute_url }}" class="bp-link">{{ service.short_name|default:service.name }}</a>
    {% endfor %}
  </div>
</section>
{% endblock %}
```

(The "philosophy" and template-generator-style "Capitalize on low hanging fruit... beta test... DevOps" strategy copy in the old template was unpublished lorem-ipsum-style filler, not real authored business copy — it's replaced here per the Global Constraints note; the genuinely authored "Our Strategies" copy is preserved in full above.)

- [ ] **Step 4: Run the tests**

Run: `python manage.py test website.tests.PageTests -v 2`
Expected: PASS for about-page-related tests.

- [ ] **Step 5: Commit**

```bash
git add templates/about.html website/tests.py
git commit -m "Rebuild the about page in the new design"
```

---

## Task 16: Blog list + detail templates

**Files:**
- Modify: `templates/blog-page.html`, `templates/blog-single.html` (overwrite existing)
- Test: `website/tests.py`

- [ ] **Step 1: Write the failing tests**

Add to `website/tests.py`, inside `PageTests`:

```python
    def test_blog_list_renders(self):
        response = self.client.get(reverse("website:blog"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.blog.title)

    def test_blog_detail_renders(self):
        response = self.client.get(self.blog.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.blog.title)
        self.assertContains(response, self.blog.author)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test website.tests.PageTests.test_blog_list_renders website.tests.PageTests.test_blog_detail_renders -v 2`
Expected: FAIL against the current templates (or pass by coincidence — the real gate is Step 4's full-suite run).

- [ ] **Step 3: Replace `templates/blog-page.html`**

```html
{% extends 'base.html' %}
{% block title %}Blog — BakPage Labs{% endblock %}
{% block content %}
<section class="bp-hero bp-hero--page">
  <div class="bp-hero__scrim bp-hero__scrim--down"></div>
  <div class="bp-container bp-hero__inner bp-hero__inner--short">
    <span class="bp-label bp-label--red">Our thinking</span>
    <h1 class="bp-h1">Notes on building software that lasts.</h1>
  </div>
</section>
<section class="bp-section bp-container">
  {% if blogs %}
  <div class="bp-grid bp-grid--3">
    {% for blog in blogs %}
    <a href="{{ blog.get_absolute_url }}" class="bp-studio-card">
      <div class="bp-post-card__img" style="background-image: url('{{ blog.image.url }}');"></div>
      <div class="bp-studio-card__body">
        <div class="bp-post-meta">
          {% for tag in blog.tags.all %}<span class="bp-tag">{{ tag.name }}</span>{% endfor %}
        </div>
        <h3>{{ blog.title }}</h3>
        <p>{{ blog.text|truncatewords:30 }}</p>
      </div>
    </a>
    {% endfor %}
  </div>
  {% else %}
  <div class="bp-empty">Nothing published yet — check back soon.</div>
  {% endif %}
</section>
{% endblock %}
```

- [ ] **Step 4: Replace `templates/blog-single.html`**

```html
{% extends 'base.html' %}
{% load humanize %}
{% block title %}{{ object.title }} — BakPage Labs{% endblock %}
{% block content %}
<section class="bp-hero bp-hero--page">
  <div class="bp-hero__scrim bp-hero__scrim--down"></div>
  <div class="bp-container bp-hero__inner bp-hero__inner--short">
    <span class="bp-label bp-label--red">Blog</span>
    <h1 class="bp-h1">{{ object.title }}</h1>
    <div class="bp-post-meta">
      <span class="bp-muted">{{ object.author }}</span>
      <span class="bp-muted">·</span>
      <span class="bp-muted">{{ object.created_at|naturaltime }}</span>
    </div>
  </div>
</section>
<section class="bp-section bp-container" style="display: grid; grid-template-columns: 1fr 0.35fr; gap: 64px;">
  <article class="bp-prose">
    {% if object.image %}
    <div class="bp-offset--media" style="margin-bottom: 32px;">
      <div class="bp-offset__inner"><img src="{{ object.image.url }}" alt="{{ object.title }}"></div>
    </div>
    {% endif %}
    {{ object.formatted_markdown|safe }}
    {% if object.quote %}
    <blockquote>
      <p>{{ object.quote }}</p>
      <footer>— {{ object.author }}</footer>
    </blockquote>
    {% endif %}
  </article>
  <aside>
    <div class="bp-panel">
      <span class="bp-label">Tags</span>
      <div class="bp-chip-row" style="margin-top: 14px;">
        {% for tag in object.tags.all %}<span class="bp-tag">{{ tag.name }}</span>{% endfor %}
      </div>
    </div>
  </aside>
</section>
{% if blog_list %}
<section class="bp-section bp-container">
  <div class="bp-heading-row"><div><span class="bp-rule"></span><h2 class="bp-h2">More posts.</h2></div></div>
  <div class="bp-grid bp-grid--3">
    {% for post in blog_list|slice:":3" %}
    {% if post.slug != object.slug %}
    <a href="{{ post.get_absolute_url }}" class="bp-studio-card">
      <div class="bp-post-card__img" style="background-image: url('{{ post.image.url }}');"></div>
      <div class="bp-studio-card__body"><h3>{{ post.title }}</h3></div>
    </a>
    {% endif %}
    {% endfor %}
  </div>
</section>
{% endif %}
{% endblock %}
```

(The old template's opening "Bring to the table win-win survival strategies..." paragraph was unpublished lorem-ipsum-style filler and is dropped, per the same Global Constraints note as Task 15.)

- [ ] **Step 5: Run the tests**

Run: `python manage.py test website.tests.PageTests -v 2`
Expected: PASS for blog-related tests.

- [ ] **Step 6: Commit**

```bash
git add templates/blog-page.html templates/blog-single.html website/tests.py
git commit -m "Rebuild blog list and detail pages in the new design"
```

---

## Task 17: Quote page template

**Files:**
- Create: `templates/quote.html`
- Modify: `static/assets/js/redesign.js`
- Test: none new — this task makes `QuoteViewTests` (already written in Task 5) pass.

**Interfaces:**
- Consumes: `QuoteView`'s context (`form`, `quote_services`, `scope_sizes`, `quote_addons`, `preselect`, `slots`, `confirmed` — Task 5), `partials/quote-calculator.html` (Task 8, rendered with `is_embedded_in_quote_form=True`).

- [ ] **Step 1: Run the not-yet-passing tests to confirm the starting point**

Run: `python manage.py test website.tests.QuoteViewTests -v 2`
Expected: FAIL with `TemplateDoesNotExist: quote.html` (as flagged in Task 5, Step 5).

- [ ] **Step 2: Add the preferred-slot chip picker to `static/assets/js/redesign.js`**

Add this new numbered section (after the contact-form section added in Task 7), and call it from `init()`:

```javascript
	/* 6. Preferred call slot picker (quote page)
	--------------------------------------------------- */
	function initSlotPicker() {
		var group = $("[data-bp-slots]");
		if (!group) return;
		var chips = $$("[data-bp-slot]", group);
		var input = document.querySelector("input[name='preferred_slot']");
		if (!input) return;

		chips.forEach(function (chip) {
			chip.addEventListener("click", function () {
				chips.forEach(function (c) {
					c.classList.toggle("is-active", c === chip);
				});
				input.value = chip.getAttribute("data-label");
			});
		});
	}
```

```javascript
	function init() {
		initNav();
		initTabs();
		initCalculators();
		initSteps();
		initContactForm();
		initSlotPicker();
	}
```

- [ ] **Step 3: Write `templates/quote.html`**

```html
{% extends 'base.html' %}
{% block title %}Get a quote — BakPage Labs{% endblock %}
{% block cta_bar %}{% endblock %}

{% block content %}
<section class="bp-hero bp-hero--page">
  <div class="bp-hero__scrim bp-hero__scrim--down"></div>
  <div class="bp-container bp-hero__inner bp-hero__inner--short">
    <span class="bp-label bp-label--red">Free, no-deck scoping call</span>
    <h1 class="bp-h1">Let's scope your project.</h1>
    <p class="bp-lead bp-measure">Pick what you're building below, tell us a bit about your business, and we'll call you at a time that works to confirm the details.</p>
  </div>
</section>

<section class="bp-section bp-container">
  {% if confirmed %}
  <div class="bp-confirm">
    <b>Thanks — we've got it.</b>
    <p>We'll call you at your preferred slot to confirm scope and next steps.</p>
  </div>
  <div class="bp-nextsteps">
    <div>
      <span class="bp-label">1. We review</span>
      <a href="{% url 'website:service' %}">See all services</a>
    </div>
    <div>
      <span class="bp-label">2. We call</span>
      <a href="tel:+25477681091">+254 777 681 091</a>
    </div>
    <div>
      <span class="bp-label">3. We start</span>
      <a href="{% url 'website:project' %}">See our work</a>
    </div>
  </div>
  {% else %}
  {% if form.errors %}
  <ul class="bp-errors">
    {% for field in form %}{% for error in field.errors %}<li>{{ field.label }}: {{ error }}</li>{% endfor %}{% endfor %}
    {% for error in form.non_field_errors %}<li>{{ error }}</li>{% endfor %}
  </ul>
  {% endif %}
  <form method="post" action="{% url 'website:quote' %}">
    {% csrf_token %}
    {% include 'partials/quote-calculator.html' with preselect=preselect is_embedded_in_quote_form=True %}
    <div class="bp-field-grid" style="margin-top: 32px;">
      {{ form.name }}
      {{ form.business }}
    </div>
    <div class="bp-field-grid">
      {{ form.email }}
      {{ form.phone }}
    </div>
    {{ form.message }}
    <span class="bp-label" style="margin-top: 24px; display: block;">Preferred call slot</span>
    <div class="bp-chip-row" data-bp-slots style="margin: 14px 0 28px;">
      {% for slot in slots %}
      <button type="button" class="bp-chip" data-bp-slot data-label="{{ slot }}">{{ slot }}</button>
      {% endfor %}
    </div>
    {{ form.preferred_slot }}
    {{ form.service }}
    {{ form.source }}
    <div class="bp-formrow">
      <button type="submit" class="bp-btn bp-btn--primary">Send enquiry</button>
    </div>
  </form>
  {% endif %}
</section>
{% endblock %}
```

- [ ] **Step 4: Run the tests**

Run: `python manage.py test website.tests.QuoteViewTests -v 2`
Expected: PASS (all 8 tests from Task 5).

Run: `python manage.py test website -v 2`
Expected: full suite PASS. If any page-level test from Tasks 6–16 still fails, fix the specific template causing it now (this is the first point every template exists, so it's the right place to catch any straggler).

- [ ] **Step 5: Commit**

```bash
git add templates/quote.html static/assets/js/redesign.js
git commit -m "Add the quote page, completing the quote-calculator feature"
```

---

## Task 18: Cleanup and final verification

**Files:**
- Delete: `wip-quote-calculator/`, `templates/partials/contact_form.html`, `templates/partials/loader.html`, `templates/partials/mobile_nav.html`
- Modify: `README.md` (remove the "In-progress work" section added earlier)
- Test: full suite + deploy checks

- [ ] **Step 1: Delete obsolete files**

```bash
git rm -r wip-quote-calculator
git rm templates/partials/contact_form.html templates/partials/loader.html templates/partials/mobile_nav.html
```

- [ ] **Step 2: Update `README.md`**

Remove the "In-progress work" section added during the earlier deployment-readiness review (it described exactly the files this plan has now finished and wired in). Leave the rest of the README as-is — it already describes local dev setup and deployment correctly.

- [ ] **Step 3: Run the full test suite**

Run: `python manage.py test -v 2`
Expected: all tests PASS (the original 17 `ContactForm`/page tests plus every test added in this plan).

- [ ] **Step 4: Run deployment checks**

Run: `python manage.py makemigrations --check --dry-run`
Expected: `No changes detected`

Run: `SECRET_KEY=temp DEBUG=False ALLOWED_HOSTS=bakpagelabs.com python manage.py check --deploy`
Expected: only the same pre-existing HSTS/SSL-redirect warnings noted in the earlier deployment review (unrelated to this work) — no new errors.

- [ ] **Step 5: Manual QA pass**

Using gstack's `/qa` or `/browse` skill, walk through: home, about, services list/detail, work list/detail (both a project with and without the new case-study fields filled in), blog list/detail, and the full quote flow (calculator → `/quote/` → submit → confirmation) at desktop and mobile widths, with and without the OS "reduce motion" setting on. Confirm the sitewide contact form in the footer still submits successfully.

- [ ] **Step 6: Final commit**

```bash
git add README.md
git commit -m "Remove finished redesign from README's in-progress section; drop obsolete WIP files"
```

---

## Self-Review Notes

**Spec coverage:** §1 shell/design decisions → Tasks 6–9; §2 data model → Task 1; §3 backend quote flow → Tasks 2–5, 8, 17; §4 shared shell → Tasks 6–9; §5 page-by-page → Tasks 12–17; §6 content-fallback rules → Task 14 (tested explicitly) plus `default:` fallbacks throughout Tasks 12–16; §7 motion layer → Tasks 10–11; §8 testing → every task adds its own tests, Task 18 runs the full suite; §9 rollout → Task 18 deletes `wip-quote-calculator/`; §10 out-of-scope items are respected (no site-stats model, no multi-step quote UI, no case-study tabs, `ContactForm` untouched).

**Placeholder scan:** no "TBD"/"implement later" remain; the one intentional literal `{# TODO #}` template comment (Task 12) is real code describing real, shippable behavior (a marked placeholder value), not a plan gap.

**Type/name consistency:** `quote_calculator_context()` (Task 5) is consumed identically by `HomeView`, `ServiceView`, and `QuoteView`; `EnquiryForm` field names (Task 3) match the hidden-input names wired in Task 8 and the `Enquiry` model fields (Task 1); `Project.metrics_list` (Task 1) is the only thing Task 14's template reads for metrics, never the raw `metrics` string.

**Review Focus coverage:** blank optional fields → Task 14's two dedicated tests; JS-disabled quote submission → Task 5's `test_calculator_fields_optional_when_js_did_not_run`; rate limiting/CSRF on the quote form → Task 5; fresh-database migration path → Task 2's pricing-seed test plus Task 1's model tests (both run against a fresh test database on every run); `base.html` swap regression safety → Task 9 runs `manage.py check` immediately and the full suite is re-verified at the end of Task 17.

---

Plan complete and saved to `docs/superpowers/plans/2026-09-28-site-redesign-quote-calculator.md`. Please review the plan. Which execution approach would you prefer?

- **Subagent-driven** — A fresh subagent implements each task and a fresh reviewer checks it before the next one starts, then a whole-branch review at the end. Most thorough; costs a fresh context per task and per review.
- **Native** — I implement every task myself in this session, the way this harness runs work, then one fresh reviewer on the most capable model checks the whole branch. Cheapest and fastest; no independent review until the end.

For this plan I recommend **subagent-driven**, because there are 18 tasks with real interface dependencies across them (the `Enquiry` model → `EnquiryForm` → `QuoteView` → `quote-calculator.html` → `quote.html` chain alone spans five tasks, and every page template depends on `base.html`'s new block structure landing correctly first) — a mistake in an early task (e.g. a wrong field name in the migration, or a hidden-input name mismatch) would silently break several later tasks' tests in confusing ways if not caught immediately by a fresh reviewer. Does the plan capture what you want, and which approach should we use?
