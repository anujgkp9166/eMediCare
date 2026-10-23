from django.contrib import admin, messages

from .models import Appointment, Doctor, DoctorSlot


class DoctorSlotInline(admin.TabularInline):
    model = DoctorSlot
    extra = 3


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("name", "specialization", "qualification", "registration_number", "clinic", "consultation_fee", "is_verified", "is_active")
    list_filter = ("is_verified", "is_active", "specialization")
    search_fields = ("name", "specialization", "clinic", "registration_number")
    list_editable = ("is_verified", "is_active")
    inlines = [DoctorSlotInline]
    actions = ["verify", "deactivate"]
    fieldsets = (
        ("Profile", {"fields": ("name", "specialization", "qualification", "registration_number", "experience_years", "languages", "photo", "bio")}),
        ("Practice", {"fields": ("clinic", "consultation_fee")}),
        ("Access & visibility", {"fields": ("user", "is_verified", "is_active")}),
    )

    @admin.action(description="Mark selected doctors as verified")
    def verify(self, request, queryset):
        queryset.update(is_verified=True)

    @admin.action(description="Hide selected doctors from patients")
    def deactivate(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "date", "time", "kind", "mode", "status")
    list_filter = ("status", "kind", "mode", "doctor", "date")
    search_fields = ("patient__username", "patient__first_name", "patient__last_name", "patient__phone", "doctor__name")
    date_hierarchy = "date"
    autocomplete_fields = ("patient", "doctor")
    list_select_related = ("patient", "doctor")
    list_editable = ("status",)
    actions = ["confirm", "complete", "cancel"]
    fieldsets = (
        ("Booking", {"fields": ("patient", "doctor", ("date", "time"), ("kind", "mode"), "reason")}),
        ("Admin control", {"fields": ("status", "meeting_link", "doctor_advice")}),
    )

    @admin.action(description="Confirm selected appointments")
    def confirm(self, request, queryset):
        n = queryset.filter(status="requested").update(status="confirmed")
        self.message_user(request, f"{n} appointment(s) confirmed.", messages.SUCCESS)

    @admin.action(description="Mark selected appointments as completed")
    def complete(self, request, queryset):
        n = queryset.exclude(status="cancelled").update(status="completed")
        self.message_user(request, f"{n} appointment(s) marked completed.", messages.SUCCESS)

    @admin.action(description="Cancel selected appointments")
    def cancel(self, request, queryset):
        n = queryset.exclude(status="completed").update(status="cancelled")
        self.message_user(request, f"{n} appointment(s) cancelled.", messages.WARNING)
