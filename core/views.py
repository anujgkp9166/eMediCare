from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from care.models import Appointment, Doctor
from diagnostics.models import Lab, LabTest, Report, Test, TestRequest

from .forms import FeedbackForm


def home(request):
    context = {
        "doctors": Doctor.objects.filter(is_active=True, is_verified=True)[:3],
        "labs": Lab.objects.filter(is_active=True, is_verified=True)[:3],
        "doctor_count": Doctor.objects.filter(is_active=True, is_verified=True).count(),
        "lab_count": Lab.objects.filter(is_active=True, is_verified=True).count(),
        "test_count": Test.objects.count(),
    }
    return render(request, "core/home.html", context)


def about(request):
    return render(request, "core/about.html")


def contact(request):
    form = FeedbackForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Thank you! Your message has reached our team. We will get back to you soon.")
        return redirect("core:contact")
    return render(request, "core/contact.html", {"form": form})


def not_found(request, exception):
    return render(request, "404.html", status=404)


@login_required
def dashboard(request):
    user = request.user
    if user.role == "doctor":
        return redirect("care:doctor_portal")
    if user.role == "lab":
        return redirect("diagnostics:lab_portal")
    if user.role == "admin" or user.is_staff:
        return redirect("admin:index")
    return _patient_dashboard(request)


def _patient_dashboard(request):
    user = request.user
    today = timezone.localdate()
    appts = Appointment.objects.filter(patient=user).select_related("doctor")
    tests = TestRequest.objects.filter(patient=user)
    reports = Report.objects.filter(test_request__patient=user)
    S = Appointment.Status
    steps = [
        ("Appointment", appts.exists()),
        ("Consultation", appts.filter(status=S.COMPLETED).exists()),
        ("Diagnostics", tests.exists()),
        ("Digital report", reports.exists()),
        ("Follow-up", appts.filter(kind=Appointment.Kind.FOLLOW_UP).exists()),
    ]
    context = {
        "steps": steps,
        "steps_done": sum(1 for _, done in steps if done),
        "appointment_count": appts.count(),
        "test_count": tests.count(),
        "report_count": reports.count(),
        "upcoming": appts.filter(date__gte=today, status__in=[S.REQUESTED, S.CONFIRMED]).order_by("date", "time").first(),
        "recent": appts[:5],
        "care_team": Doctor.objects.filter(appointments__patient=user).distinct()[:3],
    }
    return render(request, "core/patient_dashboard.html", context)
