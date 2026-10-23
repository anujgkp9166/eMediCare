from django.contrib import admin

from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "created_at", "is_resolved")
    list_filter = ("is_resolved", "created_at")
    list_editable = ("is_resolved",)
    search_fields = ("name", "email", "phone", "message")
    date_hierarchy = "created_at"
    readonly_fields = ("name", "email", "phone", "message", "created_at")
    actions = ["mark_resolved"]

    @admin.action(description="Mark selected as resolved")
    def mark_resolved(self, request, queryset):
        queryset.update(is_resolved=True)

    def has_add_permission(self, request):
        return False
