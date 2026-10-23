from datetime import date

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from accounts.decorators import role_required

from .forms import AppointmentBookingForm
from .models import Appointment, Doctor
from .services import available_times, date_in_range


def doctor_list(request):
    doctors = Doctor.objects.filter(is_active=True, is_verified=True)
    q = request.GET.get("q", "").strip()
    if q:
        doctors = doctors.filter(Q(name__icontains=q) | Q(specialization__icontains=q))
    return render(request, "care/doctor_list.html", {"doctors": doctors.distinct(), "q": q})


@require_GET
def slots_api(request):
    try:
        doctor = Doctor.objects.get(pk=int(request.GET.get("doctor", "")), is_active=True, is_verified=True)
        day = date.fromisoformat(request.GET.get("date", ""))
    except (ValueError, Doctor.DoesNotExist):
        return JsonResponse({"slots": [], "message": "Please choose a doctor and a date."})
    if not date_in_range(day):
        return JsonResponse({"slots": [], "message": "Please choose a date within the next 60 days."})
    slots = [{"value": t.strftime("%H:%M"), "label": t.strftime("%I:%M %p")} for t in available_times(doctor, day)]
    message = "" if slots else "No free times on this day. Please try another date."
    return JsonResponse({"slots": slots, "message": message})


@role_required("patient")
def appointment_list(request):
    today = timezone.localdate()
    qs = Appointment.objects.filter(patient=request.user).select_related("doctor")
    tab = request.GET.get("tab", "upcoming")
    active = [Appointment.Status.REQUESTED, Appointment.Status.CONFIRMED]
    if tab == "past":
        appts = qs.exclude(status__in=active) | qs.filter(date__lt=today)
        appts = appts.distinct().order_by("-date", "-time")
    elif tab == "all":
        appts = qs
    else:
        tab = "upcoming"
        appts = qs.filter(date__gte=today, status__in=active).order_by("date", "time")
    return render(request, "care/appointment_list.html", {"appointments": appts, "tab": tab})


@role_required("patient")
def appointment_book(request):
    initial = {}
    doctor_id = request.GET.get("doctor", "")
    if doctor_id.isdigit():
        initial["doctor"] = int(doctor_id)
    if request.GET.get("kind") in Appointment.Kind.values:
        initial["kind"] = request.GET["kind"]
    form = AppointmentBookingForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        appt = form.save(commit=False)
        appt.patient = request.user
        appt.time = form.cleaned_data["slot"]
        try:
            with transaction.atomic():
                appt.save()
        except IntegrityError:
            form.add_error("slot", "Sorry, someone just booked that time. Please pick another.")
        else:
            messages.success(request, "Your appointment request has been sent. You will see it as confirmed once our team approves it.")
            return redirect("care:appointment_detail", pk=appt.pk)
    return render(request, "care/appointment_book.html", {"form": form})


@role_required("patient")
def appointment_detail(request, pk):
    appt = get_object_or_404(Appointment.objects.select_related("doctor"), pk=pk, patient=request.user)
    return render(request, "care/appointment_detail.html", {"appt": appt})


@role_required("patient")
@require_POST
def appointment_cancel(request, pk):
    appt = get_object_or_404(Appointment, pk=pk, patient=request.user)
    if appt.can_cancel:
        appt.status = Appointment.Status.CANCELLED
        appt.save(update_fields=["status", "updated_at"])
        messages.success(request, "Your appointment has been cancelled.")
    else:
        messages.error(request, "This appointment can no longer be cancelled.")
    return redirect("care:appointment_list")


@role_required("doctor")
def doctor_portal(request):
    doctor = getattr(request.user, "doctor_profile", None)
    today = timezone.localdate()
    context = {"doctor": doctor}
    if doctor:
        qs = doctor.appointments.select_related("patient").exclude(status=Appointment.Status.CANCELLED)
        context.update(
            today_list=qs.filter(date=today).order_by("time"),
            upcoming=qs.filter(date__gt=today).order_by("date", "time")[:20],
            past=qs.filter(date__lt=today).order_by("-date", "-time")[:10],
        )
    return render(request, "care/doctor_portal.html", context)
