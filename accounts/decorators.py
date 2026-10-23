from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(*roles):
    """Allow only logged-in users whose role is in `roles`."""

    def decorator(view):
        @login_required
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                messages.info(request, "That page is not available for your account type.")
                return redirect("core:dashboard")
            return view(request, *args, **kwargs)

        return wrapper

    return decorator
