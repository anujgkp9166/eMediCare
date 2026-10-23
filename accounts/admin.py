from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "display_name", "role", "phone", "city", "is_active", "date_joined")
    list_filter = ("role", "is_active", "city")
    search_fields = ("username", "first_name", "last_name", "email", "phone")
    ordering = ("-date_joined",)
    fieldsets = BaseUserAdmin.fieldsets + (
        ("eMediCare+ profile", {"fields": ("role", "phone", "city", "gender", "date_of_birth")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("eMediCare+ profile", {"fields": ("role", "first_name", "last_name", "email", "phone", "city")}),
    )
    actions = ["activate_users", "deactivate_users"]

    @admin.display(description="Name")
    def display_name(self, obj):
        return obj.display_name

    @admin.action(description="Activate selected accounts")
    def activate_users(self, request, queryset):
        n = queryset.update(is_active=True)
        self.message_user(request, f"{n} account(s) activated.", messages.SUCCESS)

    @admin.action(description="Deactivate selected accounts (blocks login)")
    def deactivate_users(self, request, queryset):
        n = queryset.exclude(pk=request.user.pk).update(is_active=False)
        self.message_user(request, f"{n} account(s) deactivated.", messages.WARNING)
