from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.html import escape

from .models import Blog, Category, Project, Service


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
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

    def test_unknown_slug_is_404(self):
        response = self.client.get(reverse("website:service_detail", args=["nope"]))
        self.assertEqual(response.status_code, 404)

    def test_empty_optional_image_url(self):
        self.assertEqual(self.project.image1URL, "")
        self.assertEqual(Service.objects.first().imageURL, "")
