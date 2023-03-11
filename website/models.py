from django.db import models
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify
from django.shortcuts import reverse
from taggit.managers import TaggableManager


class Service(models.Model):
    name = models.CharField(max_length=30, unique=True)
    image = models.ImageField(null=True, blank=True)
    icons = models.CharField(max_length=30, blank=True, null=True)
    description = MarkdownxField()
    slug = models.SlugField()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("website:service", kwargs={
            'slug': self.slug
        })

    def formatted_markdown(self):
        return markdownify(self.description)

    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url


class Category(models.Model):
    name = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=30)
    image = models.ImageField()
    image_1 = models.ImageField(blank=True, null=True)
    image_2 = models.ImageField(blank=True, null=True)
    image_3 = models.ImageField(blank=True, null=True)
    link = models.CharField(max_length=100, blank=True, null=True)
    client = models.CharField(max_length=100, blank=True, null=True)
    description = MarkdownxField()
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, blank=True, null=True)
    slug = models.SlugField()
    tags = TaggableManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("website:project", kwargs={'slug': self.slug})

    def formatted_markdown(self):
        return markdownify(self.description)

    @property
    def image1URL(self):
        try:
            url = self.image_1.url
        except:
            url = ''
        return url

    @property
    def image2URL(self):
        try:
            url = self.image_2.url
        except:
            url = ''
        return url

    @property
    def image3URL(self):
        try:
            url = self.image_3.url
        except:
            url = ''
        return url


class Blog(models.Model):
    title = models.CharField(max_length=30)
    author = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField()
    text = MarkdownxField()
    quote = MarkdownxField()
    slug = models.SlugField()
    tags = TaggableManager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("website:blog", kwargs={'slug': self.slug})

    def formatted_markdown(self):
        return markdownify(self.text)
