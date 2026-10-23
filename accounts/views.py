from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from core.forms import StyledMixin

from .forms import DoctorRegistrationForm, LabRegistrationForm, LoginForm, PatientRegistrationForm, ProfileForm


class SiteLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


def register(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    form = PatientRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome to eMediCare+, {user.first_name}! Your account is ready.")
        return redirect("core:dashboard")
    return render(request, "accounts/register.html", {"form": form})


def _register_professional(request, form_class, template, welcome):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    form = form_class(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, welcome)
        return redirect("core:dashboard")
    return render(request, template, {"form": form})


def register_doctor(request):
    return _register_professional(
        request, DoctorRegistrationForm, "accounts/register_doctor.html",
        "Thank you, Doctor! Your profile has been sent for verification. Patients can book you once our team approves it.",
    )


def register_lab(request):
    return _register_professional(
        request, LabRegistrationForm, "accounts/register_lab.html",
        "Thank you! Your lab has been sent for verification. Our team will contact you to set up your test price list.",
    )


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form})


class SitePasswordChangeView(PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:profile")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for f in form.fields.values():
            f.widget.attrs["class"] = "input"
        return form

    def form_valid(self, form):
        messages.success(self.request, "Your password has been changed.")
        return super().form_valid(form)
