from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from core.forms import StyledMixin

from .models import User


class LoginForm(StyledMixin, AuthenticationForm):
    pass


class PatientRegistrationForm(StyledMixin, UserCreationForm):
    agree = forms.BooleanField(
        label="I understand that eMediCare+ does not diagnose, and that final medical decisions are made by my doctor.",
        error_messages={"required": "Please confirm to continue."},
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email", "phone", "city", "gender", "date_of_birth")
        widgets = {"date_of_birth": forms.DateInput(attrs={"type": "date"})}
        labels = {"username": "Choose a username", "date_of_birth": "Date of birth"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["phone"].required = True
        self.fields["email"].required = True
        self.fields["username"].help_text = "Letters, numbers and @/./+/-/_ only."

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.PATIENT
        if commit:
            user.save()
        return user


class ProfileForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone", "city", "gender", "date_of_birth")
        widgets = {"date_of_birth": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}


# ---------------------------------------------------------------------------
# Self-registration for doctors and lab partners.
# They can sign up and log in themselves, but stay hidden from patients until
# the admin verifies them (is_verified=False by default).
# ---------------------------------------------------------------------------
from datetime import time  # noqa: E402

from django.db import transaction  # noqa: E402

from care.models import WEEKDAYS, Doctor, DoctorSlot  # noqa: E402
from diagnostics.models import Lab  # noqa: E402

from .models import phone_validator  # noqa: E402

SESSIONS = [
    ("morning", "Morning (10:00 AM – 12:00 PM)"),
    ("afternoon", "Afternoon (2:00 PM – 4:00 PM)"),
]
SESSION_TIMES = {
    "morning": [time(10, 0), time(10, 30), time(11, 0), time(11, 30)],
    "afternoon": [time(14, 0), time(14, 30), time(15, 0), time(15, 30)],
}


class _ProfessionalBase(StyledMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email", "phone", "city")
        labels = {"username": "Choose a username"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("first_name", "last_name", "phone", "email"):
            self.fields[name].required = True
        self.fields["username"].help_text = "Letters, numbers and @/./+/-/_ only."


class DoctorRegistrationForm(_ProfessionalBase):
    specialization = forms.CharField(max_length=100, label="Speciality", help_text="e.g. General Physician, Paediatrician")
    qualification = forms.CharField(max_length=120, help_text="e.g. MBBS, MD")
    registration_number = forms.CharField(max_length=40, label="Medical council registration number")
    clinic = forms.CharField(max_length=150, required=False, label="Clinic / hospital name")
    experience_years = forms.IntegerField(min_value=0, max_value=70, initial=0, label="Years of experience")
    languages = forms.CharField(max_length=120, required=False, initial="Hindi, English")
    consultation_fee = forms.DecimalField(min_value=0, max_digits=8, decimal_places=2, initial=300, label="Consultation fee (₹)")
    available_days = forms.MultipleChoiceField(
        choices=WEEKDAYS, widget=forms.CheckboxSelectMultiple, initial=[0, 1, 2, 3, 4, 5], label="Days you are available"
    )
    sessions = forms.MultipleChoiceField(
        choices=SESSIONS, widget=forms.CheckboxSelectMultiple, initial=["morning"], label="Consultation sessions",
        help_text="30-minute slots are created automatically. Our team can adjust them later.",
    )
    agree = forms.BooleanField(
        label="I confirm the details are correct and I am a registered medical practitioner.",
        error_messages={"required": "Please confirm to continue."},
    )

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.DOCTOR
        user.save()
        d = self.cleaned_data
        doctor = Doctor.objects.create(
            user=user, name=user.display_name, specialization=d["specialization"], qualification=d["qualification"],
            registration_number=d["registration_number"], clinic=d["clinic"], experience_years=d["experience_years"],
            languages=d["languages"], consultation_fee=d["consultation_fee"], is_verified=False, is_active=True,
        )
        times = sorted({t for s in d["sessions"] for t in SESSION_TIMES[s]})
        DoctorSlot.objects.bulk_create(
            [DoctorSlot(doctor=doctor, weekday=int(day), start_time=t) for day in d["available_days"] for t in times]
        )
        return user


class LabRegistrationForm(_ProfessionalBase):
    lab_name = forms.CharField(max_length=150, label="Lab / diagnostic centre name")
    license_number = forms.CharField(max_length=60, label="Lab licence / registration number")
    area = forms.CharField(max_length=100, label="Area / locality")
    address = forms.CharField(max_length=250, label="Full address")
    lab_phone = forms.CharField(max_length=15, validators=[phone_validator], label="Lab phone number")
    opening_hours = forms.CharField(max_length=100, initial="7:00 AM – 8:00 PM")
    home_collection = forms.BooleanField(required=False, initial=True, label="We offer home sample collection")
    agree = forms.BooleanField(
        label="I confirm the details are correct and I am authorised to register this lab.",
        error_messages={"required": "Please confirm to continue."},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].label = "Contact person: first name"
        self.fields["last_name"].label = "Contact person: last name"

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.LAB
        user.save()
        d = self.cleaned_data
        Lab.objects.create(
            user=user, name=d["lab_name"], license_number=d["license_number"], area=d["area"], address=d["address"],
            phone=d["lab_phone"], opening_hours=d["opening_hours"], home_collection=d["home_collection"],
            is_verified=False, is_active=True,
        )
        return user
