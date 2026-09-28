from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.html import escape

from .forms import ContactForm, EnquiryForm
from .models import Blog, Category, ContactMessage, Enquiry, Project, Service


# Plain static storage so tests don't need collectstatic's manifest.
TEST_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


@override_settings(STORAGES=TEST_STORAGES)
class PageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name="Branding")
        cls.project = Project.objects.create(
            name="Azraa",
            image="azraa.png",
            description="Azraa naturals",
            category=category,
            slug="azraa",
        )
        cls.project.tags.add("branding")
        cls.blog = Blog.objects.create(
            title="Custom software",
            author="Bakpage",
            image="post.png",
            text="Some **markdown**",
            quote="A quote",
            slug="custom-software",
        )
        cls.blog.tags.add("software")

    def test_services_seeded_by_migration(self):
        self.assertEqual(Service.objects.count(), 6)
        self.assertEqual(Service.objects.first().slug, "ai-automation")

    def test_service_pricing_seeded_by_migration(self):
        service = Service.objects.get(slug="ai-automation")
        self.assertEqual(service.price_from, 85)
        self.assertEqual(service.short_name, "AI & automation")
        self.assertIn("WhatsApp & chat agents", service.highlights)

        advisory = Service.objects.get(slug="tech-advisory")
        self.assertTrue(advisory.is_retainer)
        self.assertEqual(advisory.price_from, 45)

    def test_list_pages(self):
        for name in ["home", "about", "service", "project", "blog"]:
            with self.subTest(page=name):
                response = self.client.get(reverse(f"website:{name}"))
                self.assertEqual(response.status_code, 200)

    def test_detail_pages(self):
        for obj in [Service.objects.first(), self.project, self.blog]:
            with self.subTest(obj=obj):
                response = self.client.get(obj.get_absolute_url())
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, escape(str(obj)))

    def test_no_relative_asset_paths(self):
        # Relative paths like "assets/..." or "../static/..." break on nested
        # URLs such as /service/<slug>/, so assets must use {% static %}.
        pages = [reverse(f"website:{name}") for name in ["home", "about", "service", "project", "blog"]]
        pages += [Service.objects.first().get_absolute_url(), self.project.get_absolute_url(), self.blog.get_absolute_url()]
        for url in pages:
            with self.subTest(url=url):
                html = self.client.get(url).content.decode()
                self.assertNotIn("../static/", html)
                self.assertNotIn("url('static/", html)
                self.assertNotIn('href="assets/', html)
                self.assertNotIn('data-src="assets/', html)
                self.assertNotIn('href="blog/"', html)
                self.assertIn('/static/assets/images/favicon-32x32.png"', html)

    def test_favicon_ico_redirects_to_static_file(self):
        response = self.client.get("/favicon.ico")
        self.assertRedirects(response, "/static/favicon.ico", fetch_redirect_response=False)

    def test_unknown_slug_is_404(self):
        response = self.client.get(reverse("website:service_detail", args=["nope"]))
        self.assertEqual(response.status_code, 404)

    def test_empty_optional_image_url(self):
        self.assertEqual(self.project.image1URL, "")
        self.assertEqual(Service.objects.first().imageURL, "")


@override_settings(
    CONTACT_EMAIL="info@bakpagelabs.com",
    DEFAULT_FROM_EMAIL="website@bakpagelabs.com",
    CONTACT_RATE_LIMIT=5,
    STORAGES=TEST_STORAGES,
)
class ContactFormTests(TestCase):
    url = reverse("website:contact")
    ajax = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
    data = {"name": "Jane Wanjiku", "email": "jane@example.com", "message": "I need a website."}

    def setUp(self):
        cache.clear()

    def test_form_is_on_every_page_once(self):
        response = self.client.get(reverse("website:home"))
        self.assertContains(response, 'id="pr__contact__form"', count=1)
        self.assertContains(response, f'action="{self.url}"')
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_ajax_submit_sends_email_and_stores_enquiry(self):
        response = self.client.post(self.url, self.data, **self.ajax)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ["info@bakpagelabs.com"])
        self.assertEqual(email.from_email, "website@bakpagelabs.com")
        self.assertEqual(email.reply_to, ["jane@example.com"])
        self.assertIn("Jane Wanjiku", email.subject)
        self.assertIn("I need a website.", email.body)

        enquiry = ContactMessage.objects.get()
        self.assertTrue(enquiry.email_sent)
        self.assertEqual(enquiry.ip_address, "127.0.0.1")

    def test_plain_post_redirects_back_with_message(self):
        response = self.client.post(
            self.url, self.data, HTTP_REFERER="http://testserver/about/", follow=True
        )
        self.assertRedirects(response, "http://testserver/about/")
        self.assertContains(response, "Thanks for getting in touch")
        self.assertEqual(len(mail.outbox), 1)

    def test_external_referer_is_not_followed(self):
        response = self.client.post(self.url, self.data, HTTP_REFERER="https://evil.example/")
        self.assertRedirects(response, "/")

    def test_invalid_submission_returns_errors(self):
        response = self.client.post(self.url, {"name": "", "email": "nope"}, **self.ajax)
        self.assertEqual(response.status_code, 400)
        errors = response.json()["errors"]
        self.assertEqual(set(errors), {"name", "email", "message"})
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(ContactMessage.objects.exists())

    def test_honeypot_submission_is_silently_dropped(self):
        response = self.client.post(self.url, {**self.data, "website": "http://spam"}, **self.ajax)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(ContactMessage.objects.exists())

    def test_rate_limited_per_ip(self):
        for _ in range(5):
            self.assertEqual(self.client.post(self.url, self.data, **self.ajax).status_code, 200)
        response = self.client.post(self.url, self.data, **self.ajax)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(ContactMessage.objects.count(), 5)

    def test_enquiry_kept_when_email_fails(self):
        with mock.patch("website.views.EmailMessage.send", side_effect=OSError("SMTP down")):
            with self.assertLogs("website.views", "ERROR"):
                response = self.client.post(self.url, self.data, **self.ajax)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ContactMessage.objects.get().email_sent)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_csrf_required(self):
        client = self.client_class(enforce_csrf_checks=True)
        self.assertEqual(client.post(self.url, self.data).status_code, 403)


@override_settings(STORAGES=TEST_STORAGES)
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


@override_settings(STORAGES=TEST_STORAGES)
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


class EnquiryAdminTests(TestCase):
    def test_enquiry_admin_changelist_loads(self):
        User = get_user_model()
        User.objects.create_superuser("admin", "admin@example.com", "password123")
        self.client.login(username="admin", password="password123")
        response = self.client.get(reverse("admin:website_enquiry_changelist"))
        self.assertEqual(response.status_code, 200)


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
        self.assertContains(response, "we've got it")
