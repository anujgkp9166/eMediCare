from django.contrib import messages
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from django.contrib.auth.decorators import login_required

from .forms import TestRequestForm
from .models import Lab, LabTest, Report, Test, TestRequest

SORTS = {"price": "price", "distance": "lab__distance_km", "speed": "turnaround_hours"}


def lab_list(request):
    offerings = LabTest.objects.filter(
        is_available=True, lab__is_active=True, lab__is_verified=True
    ).select_related("lab", "test")
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    sort = request.GET.get("sort", "price")
    if q:
        offerings = offerings.filter(Q(test__name__icontains=q) | Q(lab__name__icontains=q) | Q(test__category__icontains=q))
    if category:
        offerings = offerings.filter(test__category=category)
    offerings = offerings.order_by(SORTS.get(sort, "price"), "test__name")
    context = {
        "offerings": offerings,
        "labs": Lab.objects.filter(is_active=True, is_verified=True),
        "categories": Test.objects.order_by("category").values_list("category", flat=True).distinct(),
        "q": q, "category": category, "sort": sort,
    }
    return render(request, "diagnostics/lab_list.html", context)


@role_required("patient")
def request_create(request):
    initial = {}
    offering = request.GET.get("offering", "")
    if offering.isdigit():
        initial["lab_test"] = int(offering)
    form = TestRequestForm(request.POST or None, initial=initial, user=request.user)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.patient = request.user
        obj.save()
        messages.success(request, "Your test request has been received. Our team will confirm the collection details shortly.")
        return redirect("diagnostics:reports")
    return render(request, "diagnostics/request_form.html", {"form": form})


@role_required("patient")
def reports_page(request):
    requests_qs = TestRequest.objects.filter(patient=request.user).select_related(
        "lab_test__lab", "lab_test__test", "appointment__doctor"
    )
    reports = Report.objects.filter(test_request__patient=request.user).select_related(
        "test_request__lab_test__lab", "test_request__lab_test__test", "test_request__appointment__doctor", "reviewed_by"
    )
    return render(request, "diagnostics/reports.html", {
        "reports": reports,
        "requests": requests_qs.exclude(status=TestRequest.Status.REPORT_READY),
    })


@login_required
def report_file(request, pk):
    report = get_object_or_404(Report.objects.select_related("test_request__patient", "test_request__lab_test__lab"), pk=pk)
    user = request.user
    owner = report.test_request.patient_id == user.id
    lab_owner = report.test_request.lab_test.lab.user_id == user.id
    if not (owner or lab_owner or user.is_staff):
        raise Http404()
    try:
        handle = report.file.open("rb")
    except FileNotFoundError:
        raise Http404("The report file is missing.")
    return FileResponse(handle, as_attachment=False)


@role_required("lab")
def lab_portal(request):
    lab = getattr(request.user, "lab_profile", None)
    qs = TestRequest.objects.none()
    if lab:
        qs = TestRequest.objects.filter(lab_test__lab=lab).select_related("patient", "lab_test__test")
    active = qs.exclude(status__in=[TestRequest.Status.REPORT_READY, TestRequest.Status.CANCELLED])
    done = qs.filter(status=TestRequest.Status.REPORT_READY)[:15]
    return render(request, "diagnostics/lab_portal.html", {"lab": lab, "active": active, "done": done})
