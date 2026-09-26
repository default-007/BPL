from django.contrib import admin
from markdownx.admin import MarkdownxModelAdmin

from .models import Blog, Category, ContactMessage, Project, Service

admin.site.register(Service, MarkdownxModelAdmin)
admin.site.register(Project, MarkdownxModelAdmin)
admin.site.register(Blog, MarkdownxModelAdmin)
admin.site.register(Category)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at", "email_sent")
    list_filter = ("email_sent", "created_at")
    search_fields = ("name", "email", "message")
    readonly_fields = ("name", "email", "message", "created_at", "ip_address", "email_sent")
