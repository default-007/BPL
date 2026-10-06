from django.contrib import admin
from markdownx.admin import MarkdownxModelAdmin

from .models import Blog, Category, ContactMessage, Enquiry, Project, Service

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
