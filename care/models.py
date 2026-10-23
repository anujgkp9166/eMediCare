from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

WEEKDAYS = [
    (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"),
    (4, "Friday"), (5, "Saturday"), (6, "Sunday"),
]


class Doctor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="doctor_profile", limit_choices_to={"role": "doctor"},
        help_text="Optional. Link a doctor login so the doctor can see their own schedule.",
    )
    name = models.CharField(max_length=120, help_text="Without 'Dr.' (it is added automatically).")
    specialization = models.CharField(max_length=100, default="General Physician")
    qualification = models.CharField(max_length=120, blank=True, help_text="e.g. MBBS, MD")
    registration_number = models.CharField(max_length=40, blank=True, help_text="Medical council registration number (check before verifying).")
    clinic = models.CharField(max_length=150, blank=True)
    experience_years = models.PositiveSmallIntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    languages = models.CharField(max_length=120, blank=True, default="Hindi, English")
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to="doctors/", blank=True)
    is_verified = models.BooleanField(default=True, help_text="Only verified doctors are shown to patients.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    @property
    def display_name(self):
        return self.name if self.name.lower().startswith("dr") else f"Dr. {self.name}"

    @property
    def initials(self):
        parts = [p for p in self.name.replace("Dr.", "").split() if p]
        return "".join(p[0] for p in parts[:2]).upper() or "D"

    def __str__(self):
        return f"{self.display_name} · {self.specialization}"


class DoctorSlot(models.Model):
    """A weekly repeating consultation time for a doctor."""

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="slots")
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAYS)
    start_time = models.TimeField()

    class Meta:
        ordering = ["weekday", "start_time"]
        unique_together = [("doctor", "weekday", "start_time")]

    def __str__(self):
        return f"{self.get_weekday_display()} {self.start_time:%I:%M %p}"


class Appointment(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Awaiting confirmation"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class Kind(models.TextChoices):
        CONSULTATION = "consultation", "Consultation"
        FOLLOW_UP = "follow_up", "Follow-up"

    class Mode(models.TextChoices):
        ONLINE = "online", "Online consultation"
        CLINIC = "clinic", "Clinic visit"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="appointments",
        limit_choices_to={"role": "patient"},
    )
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, related_name="appointments")
    date = models.DateField()
    time = models.TimeField()
    kind = models.CharField(max_length=15, choices=Kind.choices, default=Kind.CONSULTATION)
    mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.ONLINE)
    reason = models.TextField(blank=True, max_length=600, help_text="Patient's reason for visit.")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.REQUESTED)
    meeting_link = models.URLField(blank=True, help_text="Video-call link, shared with the patient once confirmed.")
    doctor_advice = models.TextField(blank=True, help_text="Doctor's advice / prescription notes. Visible to the patient.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-time"]
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "date", "time"],
                condition=~Q(status="cancelled"),
                name="unique_active_doctor_slot",
                violation_error_message="This doctor already has an appointment at that time.",
            )
        ]

    @property
    def can_cancel(self):
        return self.status in (self.Status.REQUESTED, self.Status.CONFIRMED) and self.date >= timezone.localdate()

    def __str__(self):
        return f"{self.patient.display_name} with {self.doctor.display_name} · {self.date:%d %b %Y} {self.time:%I:%M %p}"
