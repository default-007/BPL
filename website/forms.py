from django import forms

from .models import ContactMessage, Enquiry


class ContactForm(forms.ModelForm):
    # Honeypot: hidden from people with CSS, but bots tend to fill it in.
    website = forms.CharField(required=False)

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "message"]

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) > 5000:
            raise forms.ValidationError("Please keep your message under 5000 characters.")
        return message

    def is_spam(self):
        return bool(self.cleaned_data.get("website"))


class EnquiryForm(forms.ModelForm):
    """Backs both the full quote flow and the short enquiry form on a service page."""

    class Meta:
        model = Enquiry
        fields = [
            "name",
            "business",
            "email",
            "phone",
            "message",
            "service",
            "scope_kind",
            "scope_size",
            "addons",
            "estimate",
            "preferred_slot",
            "source",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your name"}),
            "business": forms.TextInput(attrs={"placeholder": "Business name"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email"}),
            "phone": forms.TextInput(attrs={"placeholder": "WhatsApp / phone"}),
            "message": forms.Textarea(
                attrs={"placeholder": "What are you trying to fix or launch?"}
            ),
            "service": forms.HiddenInput(),
            "scope_kind": forms.HiddenInput(),
            "scope_size": forms.HiddenInput(),
            "addons": forms.HiddenInput(),
            "estimate": forms.HiddenInput(),
            "preferred_slot": forms.HiddenInput(),
            "source": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.HiddenInput):
                field.widget.attrs.setdefault("class", "bp-field")
        self.fields["message"].label = "What are you trying to fix or launch?"
