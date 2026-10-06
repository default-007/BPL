from django.db import models
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify
from django.urls import reverse
from taggit.managers import TaggableManager


class Service(models.Model):
    name = models.CharField(max_length=60, unique=True)
    tagline = models.CharField(max_length=120, blank=True, null=True)
    image = models.ImageField(null=True, blank=True)
    icons = models.CharField(max_length=30, blank=True, null=True)
    description = MarkdownxField()
    slug = models.SlugField()
    order = models.PositiveIntegerField(default=0)
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

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("website:service_detail", kwargs={"slug": self.slug})

    def formatted_markdown(self):
        return markdownify(self.description)

    @property
    def imageURL(self):
        try:
            url = self.image.url
        except ValueError:
            url = ""
        return url


class Category(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=150)
    image = models.ImageField()
    image_1 = models.ImageField(blank=True, null=True)
    image_2 = models.ImageField(blank=True, null=True)
    image_3 = models.ImageField(blank=True, null=True)
    link = models.CharField(max_length=100, blank=True, null=True)
    client = models.CharField(max_length=100, blank=True, null=True)
    description = MarkdownxField()
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, blank=True, null=True
    )
    slug = models.SlugField()
    tags = TaggableManager()
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

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("website:project_detail", kwargs={"slug": self.slug})

    def formatted_markdown(self):
        return markdownify(self.description)

    @property
    def image1URL(self):
        try:
            url = self.image_1.url
        except ValueError:
            url = ""
        return url

    @property
    def image2URL(self):
        try:
            url = self.image_2.url
        except ValueError:
            url = ""
        return url

    @property
    def image3URL(self):
        try:
            url = self.image_3.url
        except ValueError:
            url = ""
        return url

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


class Blog(models.Model):
    title = models.CharField(max_length=300)
    author = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField()
    text = MarkdownxField()
    quote = MarkdownxField()
    slug = models.SlugField()
    tags = TaggableManager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("website:blog_detail", kwargs={"slug": self.slug})

    def formatted_markdown(self):
        return markdownify(self.text)


class ContactMessage(models.Model):
    """An enquiry sent through the site's contact form.

    Stored so no lead is lost if the notification email can't be delivered.
    """

    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    email_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} <{self.email}>"


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
