from django.conf import settings


def site(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_TAGLINE": settings.SITE_TAGLINE,
        "SITE_MOTTO": settings.SITE_MOTTO,
        "ORGANISATION": settings.ORGANISATION,
        "SITE_LOCATION": settings.SITE_LOCATION,
        "CONTACT_EMAIL": settings.CONTACT_EMAIL,
        "CONTACT_PHONE": settings.CONTACT_PHONE,
    }
