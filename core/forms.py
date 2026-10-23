from django import forms

from .models import Feedback


class StyledMixin:
    """Adds the site's CSS classes to every widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxSelectMultiple):
                continue
            css = "check" if isinstance(widget, forms.CheckboxInput) else "input"
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css}".strip()


class FeedbackForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ("name", "email", "phone", "message")
        labels = {"name": "Your name", "message": "How can we help?"}
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}

    def clean(self):
        data = super().clean()
        if not data.get("email") and not data.get("phone"):
            raise forms.ValidationError("Please share an email or phone number so we can reply.")
        return data
