from django.urls import path

from . import views

app_name = "care"

urlpatterns = [
    path("doctors/", views.doctor_list, name="doctor_list"),
    path("appointments/", views.appointment_list, name="appointment_list"),
    path("appointments/book/", views.appointment_book, name="book"),
    path("appointments/slots/", views.slots_api, name="slots"),
    path("appointments/<int:pk>/", views.appointment_detail, name="appointment_detail"),
    path("appointments/<int:pk>/cancel/", views.appointment_cancel, name="appointment_cancel"),
    path("doctor-portal/", views.doctor_portal, name="doctor_portal"),
]
