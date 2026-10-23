from django.db import models

from accounts.models import phone_validator


class Feedback(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True, validators=[phone_validator])
    message = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    admin_note = models.TextField(blank=True, help_text="Internal note, not shown to the sender.")

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "feedback"

    def __str__(self):
        return f"{self.name} · {self.created_at:%d %b %Y}"
