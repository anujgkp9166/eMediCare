from django.contrib.admin.apps import AdminConfig


class EmediAdminConfig(AdminConfig):
    default_site = "core.admin_site.EmediAdminSite"
