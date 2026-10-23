from django.contrib.admin import AdminSite
from django.urls import reverse
from django.utils import timezone


class EmediAdminSite(AdminSite):
    site_header = "eMediCare+ Control Centre"
    site_title = "eMediCare+ Admin"
    index_title = "Operations overview"

    def index(self, request, extra_context=None):
        from accounts.models import User
        from care.models import Appointment, Doctor
        from core.models import Feedback
        from diagnostics.models import Lab, Report, TestRequest

        today = timezone.localdate()

        def url(name, query=""):
            return reverse(f"{self.name}:{name}") + query

        stats = [
            {"label": "Patients", "value": User.objects.filter(role="patient").count(),
             "url": url("accounts_user_changelist", "?role__exact=patient")},
            {"label": "Doctors", "value": Doctor.objects.filter(is_active=True, is_verified=True).count(),
             "url": url("care_doctor_changelist", "?is_verified__exact=1")},
            {"label": "Doctors awaiting approval", "value": Doctor.objects.filter(is_verified=False).count(), "alert": True,
             "url": url("care_doctor_changelist", "?is_verified__exact=0")},
            {"label": "Partner labs", "value": Lab.objects.filter(is_active=True, is_verified=True).count(),
             "url": url("diagnostics_lab_changelist", "?is_verified__exact=1")},
            {"label": "Labs awaiting approval", "value": Lab.objects.filter(is_verified=False).count(), "alert": True,
             "url": url("diagnostics_lab_changelist", "?is_verified__exact=0")},
            {"label": "Appointments to confirm",
             "value": Appointment.objects.filter(status="requested").count(), "alert": True,
             "url": url("care_appointment_changelist", "?status__exact=requested")},
            {"label": "Appointments today", "value": Appointment.objects.filter(date=today).exclude(status="cancelled").count(),
             "url": url("care_appointment_changelist", f"?date__day={today.day}&date__month={today.month}&date__year={today.year}")},
            {"label": "Test requests pending",
             "value": TestRequest.objects.filter(status="requested").count(), "alert": True,
             "url": url("diagnostics_testrequest_changelist", "?status__exact=requested")},
            {"label": "Reports uploaded", "value": Report.objects.count(),
             "url": url("diagnostics_report_changelist")},
            {"label": "Open feedback", "value": Feedback.objects.filter(is_resolved=False).count(),
             "url": url("core_feedback_changelist", "?is_resolved__exact=0")},
        ]
        context = {
            "stats": stats,
            "pending_appointments": Appointment.objects.filter(status="requested")
            .select_related("patient", "doctor").order_by("date", "time")[:6],
            "pending_requests": TestRequest.objects.filter(status="requested")
            .select_related("patient", "lab_test__lab", "lab_test__test").order_by("-created_at")[:6],
        }
        context.update(extra_context or {})
        return super().index(request, context)
