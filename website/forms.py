from django import forms

from .models import ContactMessage


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
