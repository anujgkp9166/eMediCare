from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone

from .storage import private_storage


class Lab(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="lab_profile", limit_choices_to={"role": "lab"},
        help_text="Optional. Link a lab login so the lab can see its own requests.",
    )
    name = models.CharField(max_length=150)
    area = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=250, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    license_number = models.CharField(max_length=60, blank=True, help_text="Lab licence / registration number (check before verifying).")
    opening_hours = models.CharField(max_length=100, blank=True, default="7:00 AM – 8:00 PM")
    distance_km = models.DecimalField(max_digits=4, decimal_places=1, default=0, help_text="Approx. distance from town centre.")
    home_collection = models.BooleanField(default=True, help_text="Does this lab offer home sample collection?")
    is_verified = models.BooleanField(default=True, help_text="Only verified labs are shown to patients.")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["distance_km", "name"]

    def __str__(self):
        return self.name


class Test(models.Model):
    name = models.CharField(max_length=120, unique=True)
    category = models.CharField(max_length=60, default="Blood test")
    description = models.TextField(blank=True)
    preparation = models.CharField(max_length=200, blank=True, help_text="e.g. 8–10 hours fasting")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class LabTest(models.Model):
    """A test offered by a lab, with that lab's price."""

    lab = models.ForeignKey(Lab, on_delete=models.CASCADE, related_name="offerings")
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="offerings")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    turnaround_hours = models.PositiveSmallIntegerField(default=24, help_text="Hours until the report is ready.")
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ["test__name", "price"]
        unique_together = [("lab", "test")]
        verbose_name = "lab price list entry"
        verbose_name_plural = "lab price list"

    def __str__(self):
        return f"{self.test.name} at {self.lab.name} (₹{self.price:.0f})"


class TestRequest(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Request received"
        SCHEDULED = "scheduled", "Collection scheduled"
        COLLECTED = "collected", "Sample collected"
        REPORT_READY = "report_ready", "Report ready"
        CANCELLED = "cancelled", "Cancelled"

    class Collection(models.TextChoices):
        HOME = "home", "Home sample collection"
        LAB = "lab", "Visit the lab"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="test_requests",
        limit_choices_to={"role": "patient"},
    )
    lab_test = models.ForeignKey(LabTest, on_delete=models.PROTECT, related_name="requests", verbose_name="test")
    appointment = models.ForeignKey(
        "care.Appointment", null=True, blank=True, on_delete=models.SET_NULL, related_name="test_requests",
        help_text="The doctor visit that recommended this test.",
    )
    collection_type = models.CharField(max_length=5, choices=Collection.choices, default=Collection.HOME)
    preferred_date = models.DateField()
    address = models.TextField(blank=True, max_length=400, help_text="Pickup address for home collection.")
    notes = models.TextField(blank=True, max_length=400)
    status = models.CharField(max_length=14, choices=Status.choices, default=Status.REQUESTED)
    scheduled_slot = models.CharField(max_length=80, blank=True, help_text="e.g. 24 Oct, 8–10 AM. Shown to the patient.")
    collection_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def total_price(self):
        return self.lab_test.price + self.collection_fee

    def __str__(self):
        return f"{self.lab_test.test.name} for {self.patient.display_name}"


class Report(models.Model):
    test_request = models.OneToOneField(TestRequest, on_delete=models.CASCADE, related_name="report")
    file = models.FileField(
        upload_to="reports/%Y/%m/", storage=private_storage,
        validators=[FileExtensionValidator(["pdf", "png", "jpg", "jpeg"])],
        help_text="PDF or image, up to 5 MB.",
    )
    summary = models.TextField(blank=True, help_text="Short note from the lab. Not a diagnosis.")
    reported_on = models.DateField(default=timezone.localdate)
    reviewed_by = models.ForeignKey("care.Doctor", null=True, blank=True, on_delete=models.SET_NULL, related_name="reviewed_reports")
    doctor_remarks = models.TextField(blank=True, help_text="Doctor's remarks after review. Visible to the patient.")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-reported_on", "-uploaded_at"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        req = self.test_request
        if req.status not in (TestRequest.Status.REPORT_READY, TestRequest.Status.CANCELLED):
            req.status = TestRequest.Status.REPORT_READY
            req.save(update_fields=["status", "updated_at"])

    def __str__(self):
        return f"Report: {self.test_request}"
