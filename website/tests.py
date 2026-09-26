from unittest import mock

from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.html import escape

from .models import Blog, Category, ContactMessage, Project, Service


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
