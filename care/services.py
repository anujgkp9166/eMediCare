from datetime import timedelta

from django.utils import timezone

from .models import Appointment

MAX_DAYS_AHEAD = 60


def available_times(doctor, day):
    """Free slot times (datetime.time) for `doctor` on `day`."""
    slots = doctor.slots.filter(weekday=day.weekday())
    booked = set(
        Appointment.objects.filter(doctor=doctor, date=day)
        .exclude(status=Appointment.Status.CANCELLED)
        .values_list("time", flat=True)
    )
    now = timezone.localtime()
    free = []
    for slot in slots:
        if slot.start_time in booked:
            continue
        if day == now.date() and slot.start_time <= now.time():
            continue
        free.append(slot.start_time)
    return free


def date_in_range(day):
    today = timezone.localdate()
    return today <= day <= today + timedelta(days=MAX_DAYS_AHEAD)
