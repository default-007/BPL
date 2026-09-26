from django.contrib import admin
from markdownx.admin import MarkdownxModelAdmin

from .models import Blog, Category, Project, Service

admin.site.register(Service, MarkdownxModelAdmin)
admin.site.register(Project, MarkdownxModelAdmin)
admin.site.register(Blog, MarkdownxModelAdmin)
admin.site.register(Category)
