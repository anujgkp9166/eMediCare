from django import forms
from django.utils import timezone

from care.models import Appointment
from core.forms import StyledMixin

from .models import LabTest, TestRequest


class LabTestChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.test.name} · {obj.lab.name} · ₹{obj.price:.0f}"


class AppointmentChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.doctor.display_name} · {obj.date:%d %b %Y}"


class TestRequestForm(StyledMixin, forms.ModelForm):
    lab_test = LabTestChoiceField(queryset=LabTest.objects.none(), label="Test and lab", empty_label="Select a test")
    appointment = AppointmentChoiceField(
        queryset=Appointment.objects.none(), required=False, empty_label="Not linked to a visit",
        label="Doctor visit that recommended this test (optional)",
    )

    class Meta:
        model = TestRequest
        fields = ("lab_test", "appointment", "collection_type", "preferred_date", "address", "notes")
        labels = {"collection_type": "How would you like to give the sample?", "preferred_date": "Preferred date",
                  "address": "Home address for sample pickup", "notes": "Anything we should know? (optional)"}
        widgets = {
            "preferred_date": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lab_test"].queryset = LabTest.objects.filter(
            is_available=True, lab__is_active=True, lab__is_verified=True
        ).select_related("lab", "test")
        if user is not None:
            self.fields["appointment"].queryset = Appointment.objects.filter(
                patient=user, status=Appointment.Status.COMPLETED
            ).select_related("doctor")
        self.fields["preferred_date"].widget.attrs["min"] = timezone.localdate().isoformat()

    def clean_preferred_date(self):
        day = self.cleaned_data["preferred_date"]
        if day < timezone.localdate():
            raise forms.ValidationError("Please choose today or a future date.")
        return day

    def clean(self):
        data = super().clean()
        offering = data.get("lab_test")
        if data.get("collection_type") == TestRequest.Collection.HOME:
            if not (data.get("address") or "").strip():
                self.add_error("address", "Please enter your address for home collection.")
            if offering and not offering.lab.home_collection:
                self.add_error("collection_type", "This lab does not offer home collection. Choose 'Visit the lab' or another lab.")
        return data
