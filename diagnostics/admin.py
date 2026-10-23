from django.contrib import admin, messages

from .models import Lab, LabTest, Report, Test, TestRequest


class LabTestInline(admin.TabularInline):
    model = LabTest
    extra = 2
    autocomplete_fields = ("test",)


@admin.register(Lab)
class LabAdmin(admin.ModelAdmin):
    list_display = ("name", "area", "phone", "license_number", "distance_km", "home_collection", "is_verified", "is_active")
    list_filter = ("is_verified", "is_active", "home_collection")
    list_editable = ("is_verified", "is_active")
    search_fields = ("name", "area", "address", "phone")
    inlines = [LabTestInline]
    fieldsets = (
        ("Lab details", {"fields": ("name", "area", "address", "phone", "license_number", "opening_hours", "distance_km")}),
        ("Services", {"fields": ("home_collection",)}),
        ("Access & visibility", {"fields": ("user", "is_verified", "is_active")}),
    )


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "preparation")
    list_filter = ("category",)
    search_fields = ("name", "category")


@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ("test", "lab", "price", "turnaround_hours", "is_available")
    list_filter = ("lab", "is_available", "test__category")
    list_editable = ("price", "turnaround_hours", "is_available")
    search_fields = ("test__name", "lab__name")
    autocomplete_fields = ("lab", "test")


class ReportInline(admin.StackedInline):
    model = Report
    extra = 0
    max_num = 1
    autocomplete_fields = ("reviewed_by",)


@admin.register(TestRequest)
class TestRequestAdmin(admin.ModelAdmin):
    list_display = ("patient", "lab_test", "collection_type", "preferred_date", "scheduled_slot", "status", "created_at")
    list_filter = ("status", "collection_type", "lab_test__lab", "preferred_date")
    search_fields = ("patient__username", "patient__first_name", "patient__phone", "lab_test__test__name", "lab_test__lab__name")
    date_hierarchy = "created_at"
    autocomplete_fields = ("patient", "lab_test", "appointment")
    list_select_related = ("patient", "lab_test__lab", "lab_test__test")
    inlines = [ReportInline]
    actions = ["mark_scheduled", "mark_collected", "mark_cancelled"]
    fieldsets = (
        ("Request", {"fields": ("patient", "lab_test", "appointment", ("collection_type", "preferred_date"), "address", "notes")}),
        ("Admin control", {"fields": ("status", "scheduled_slot", "collection_fee")}),
    )

    @admin.action(description="Mark as collection scheduled")
    def mark_scheduled(self, request, queryset):
        n = queryset.filter(status="requested").update(status="scheduled")
        self.message_user(request, f"{n} request(s) scheduled.", messages.SUCCESS)

    @admin.action(description="Mark as sample collected")
    def mark_collected(self, request, queryset):
        n = queryset.filter(status__in=["requested", "scheduled"]).update(status="collected")
        self.message_user(request, f"{n} request(s) marked collected.", messages.SUCCESS)

    @admin.action(description="Cancel selected requests")
    def mark_cancelled(self, request, queryset):
        n = queryset.exclude(status="report_ready").update(status="cancelled")
        self.message_user(request, f"{n} request(s) cancelled.", messages.WARNING)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("test_request", "reported_on", "reviewed_by", "uploaded_at")
    list_filter = ("reported_on", "reviewed_by")
    search_fields = ("test_request__patient__username", "test_request__patient__first_name", "test_request__lab_test__test__name")
    autocomplete_fields = ("test_request", "reviewed_by")
    date_hierarchy = "reported_on"
