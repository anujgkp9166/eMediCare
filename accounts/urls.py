from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.SiteLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("register/doctor/", views.register_doctor, name="register_doctor"),
    path("register/lab/", views.register_lab, name="register_lab"),
    path("profile/", views.profile, name="profile"),
    path("password/", views.SitePasswordChangeView.as_view(), name="password_change"),
]
