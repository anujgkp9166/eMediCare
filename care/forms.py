from datetime import datetime, timedelta

from django import forms
from django.utils import timezone

from core.forms import StyledMixin

from .models import Appointment, Doctor
from .services import MAX_DAYS_AHEAD, available_times, date_in_range


class AppointmentBookingForm(StyledMixin, forms.ModelForm):
    slot = forms.ChoiceField(label="Time", choices=[("", "Choose a doctor and date first")])

    class Meta:
        model = Appointment
        fields = ("doctor", "date", "kind", "mode", "reason")
        labels = {"reason": "What would you like to discuss? (optional)", "kind": "Visit type", "mode": "How would you like to consult?"}
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "reason": forms.Textarea(attrs={"rows": 3, "placeholder": "Briefly describe your concern"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["doctor"].queryset = Doctor.objects.filter(is_active=True, is_verified=True)
        self.fields["doctor"].empty_label = "Select a doctor"
        today = timezone.localdate()
        self.fields["date"].widget.attrs["min"] = today.isoformat()
        self.fields["date"].widget.attrs["max"] = (today + timedelta(days=MAX_DAYS_AHEAD)).isoformat()
        chosen = self.data.get("slot", "") if self.is_bound else ""
        self.fields["slot"].widget.attrs["data-selected"] = chosen
        if self.is_bound:
            doctor, day = self._parse_doctor_date()
            if doctor and day:
                self.fields["slot"].choices = [("", "Choose a time")] + [
                    (t.strftime("%H:%M"), t.strftime("%I:%M %p")) for t in available_times(doctor, day)
                ]

    def _parse_doctor_date(self):
        try:
            doctor = Doctor.objects.get(pk=int(self.data.get("doctor")), is_active=True, is_verified=True)
            day = datetime.strptime(self.data.get("date", ""), "%Y-%m-%d").date()
            return doctor, day
        except (TypeError, ValueError, Doctor.DoesNotExist):
            return None, None

    def clean_date(self):
        day = self.cleaned_data["date"]
        if not date_in_range(day):
            raise forms.ValidationError(f"Please choose a date within the next {MAX_DAYS_AHEAD} days.")
        return day

    def clean(self):
        data = super().clean()
        doctor, day, value = data.get("doctor"), data.get("date"), data.get("slot")
        if doctor and day and value:
            chosen = datetime.strptime(value, "%H:%M").time()
            if chosen not in available_times(doctor, day):
                self.add_error("slot", "That time is no longer available. Please pick another.")
            else:
                data["slot"] = chosen
        return data
