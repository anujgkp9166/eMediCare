from django.conf import settings
from django.core.files.storage import FileSystemStorage


def private_storage():
    """Reports live outside the public media folder and are served only through a permission-checked view."""
    return FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT)
