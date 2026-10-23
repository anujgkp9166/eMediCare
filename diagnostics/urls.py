from django.urls import path

from . import views

app_name = "diagnostics"

urlpatterns = [
    path("labs/", views.lab_list, name="lab_list"),
    path("tests/request/", views.request_create, name="request_create"),
    path("reports/", views.reports_page, name="reports"),
    path("reports/<int:pk>/file/", views.report_file, name="report_file"),
    path("lab-portal/", views.lab_portal, name="lab_portal"),
]
