import logging

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import DetailView, ListView, View

from . import pricing
from .forms import ContactForm, EnquiryForm
from .models import Blog, Project, Service

logger = logging.getLogger(__name__)


def quote_calculator_context():
    """Context shared by every template that includes quote-calculator.html."""
    quote_services = [
        {
            "slug": service.slug,
            "label": service.short_name or service.name,
            "price_from": service.price_from,
            "addon_factor": service.addon_factor,
            "is_retainer": service.is_retainer,
        }
        for service in Service.objects.all()
    ]
    return {
        "quote_services": quote_services,
        "scope_sizes": pricing.SCOPE_SIZES,
        "quote_addons": pricing.QUOTE_ADDONS,
    }


class HomeView(View):
    def get(self, request):
        services = Service.objects.all()
        projects = Project.objects.all()
        blogs = Blog.objects.all()
        template_name = "home.html"
        context = {'services': services, 'projects': projects, 'blogs': blogs}
        context.update(quote_calculator_context())
        return render(request, template_name, context)

class LandingPage(View):
    def get(self, request, *args, **kwargs):
        template_name = "new/main.html"
        return render(request, template_name,)

class AboutView(View):
    def get(self, request):
        services = Service.objects.all()
        template_name = "about.html"
        context = {'services': services,}
        return render(request, template_name, context)


class ServiceView(DetailView):
    model = Service
    template_name = "service-single.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service_list'] = Service.objects.all()
        context.update(quote_calculator_context())
        return context


class ProjectDetailView(DetailView):
    model = Project
    template_name = "project-single.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project_list'] = Project.objects.all()
        return context


class ProjectListView(ListView):
    model = Project
    template_name = "project-list.html"

class ServiceListView(ListView):
    model = Service
    template_name = "service-list.html"

class BlogView(View):
    def get(self, request):
        blogs = Blog.objects.all()
        template_name = "blog-page.html"
        context = {'blogs': blogs}
        return render(request, template_name, context)


class BlogDetailView(DetailView):
    model = Blog
    template_name = "blog-single.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['blog_list'] = Blog.objects.all()
        return context


class ContactView(View):
    """Handle the contact form: store the enquiry and email it to CONTACT_EMAIL.

    Responds with JSON to the site's AJAX submit, and with a redirect plus a
    flash message when JavaScript is off.
    """

    http_method_names = ["post"]
    success_message = "Thanks for getting in touch! We'll get back to you shortly."
    error_message = "Please check the highlighted fields and try again."
    throttled_message = "You've sent several messages already. Please try again later."

    def post(self, request):
        form = ContactForm(request.POST)
        if not form.is_valid():
            return self.respond(request, False, self.error_message, form.errors, status=400)

        # Pretend a bot submission succeeded so it doesn't retry.
        if form.is_spam():
            return self.respond(request, True, self.success_message)

        ip = request.META.get("REMOTE_ADDR")
        if self.is_throttled(ip):
            return self.respond(request, False, self.throttled_message, status=429)

        enquiry = form.save(commit=False)
        enquiry.ip_address = ip
        enquiry.save()

        try:
            self.send_notification(enquiry)
        except Exception:
            # The enquiry is saved, so it can still be read in the admin.
            logger.exception("Could not send contact email for enquiry %s", enquiry.pk)
        else:
            enquiry.email_sent = True
            enquiry.save(update_fields=["email_sent"])

        return self.respond(request, True, self.success_message)

    def is_throttled(self, ip):
        key = f"contact-form:{ip}"
        count = cache.get(key, 0)
        if count >= settings.CONTACT_RATE_LIMIT:
            return True
        cache.set(key, count + 1, 60 * 60)
        return False

    def send_notification(self, enquiry):
        body = (
            f"New enquiry from the website\n\n"
            f"Name: {enquiry.name}\n"
            f"Email: {enquiry.email}\n\n"
            f"{enquiry.message}\n"
        )
        EmailMessage(
            subject=f"Website enquiry from {enquiry.name}",
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.CONTACT_EMAIL],
            reply_to=[enquiry.email],
        ).send()

    def respond(self, request, ok, message, errors=None, status=200):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {"ok": ok, "message": message, "errors": errors or {}}, status=status
            )

        (messages.success if ok else messages.error)(request, message)
        next_url = request.META.get("HTTP_REFERER")
        if not url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            next_url = "website:home"
        return redirect(next_url)


class QuoteView(View):
    """Render the quote calculator page and handle its enquiry submission."""

    success_message = "Thanks — we've got it. We'll call you at your preferred slot to confirm scope."
    error_message = "Please check the highlighted fields and try again."
    throttled_message = "You've sent several enquiries already. Please try again later."

    def get(self, request):
        initial = {"source": "quote"}
        preselect = None
        slug = request.GET.get("service")
        if slug:
            service = Service.objects.filter(slug=slug).first()
            if service:
                initial["service"] = service.pk
                preselect = service.slug
        form = EnquiryForm(initial=initial)
        context = self.build_context(form)
        context["preselect"] = preselect
        context["slots"] = pricing.upcoming_slots()
        return render(request, "quote.html", context)

    def post(self, request):
        form = EnquiryForm(request.POST)
        if not form.is_valid():
            if self.is_ajax(request):
                return JsonResponse(
                    {"ok": False, "message": self.error_message, "errors": form.errors},
                    status=400,
                )
            context = self.build_context(form)
            context["slots"] = pricing.upcoming_slots()
            return render(request, "quote.html", context, status=400)

        ip = request.META.get("REMOTE_ADDR")
        if self.is_throttled(ip):
            if self.is_ajax(request):
                return JsonResponse({"ok": False, "message": self.throttled_message}, status=429)
            context = self.build_context(EnquiryForm())
            context["slots"] = pricing.upcoming_slots()
            return render(request, "quote.html", context, status=429)

        enquiry = form.save()

        try:
            self.send_notification(enquiry)
        except Exception:
            logger.exception("Could not send quote notification email for enquiry %s", enquiry.pk)

        if self.is_ajax(request):
            return JsonResponse({"ok": True, "message": self.success_message})

        context = self.build_context(EnquiryForm())
        context["slots"] = pricing.upcoming_slots()
        context["confirmed"] = True
        return render(request, "quote.html", context)

    def build_context(self, form):
        context = quote_calculator_context()
        context["form"] = form
        return context

    def is_throttled(self, ip):
        key = f"quote-form:{ip}"
        count = cache.get(key, 0)
        if count >= settings.CONTACT_RATE_LIMIT:
            return True
        cache.set(key, count + 1, 60 * 60)
        return False

    def is_ajax(self, request):
        return request.headers.get("x-requested-with") == "XMLHttpRequest"

    def send_notification(self, enquiry):
        lines = [
            "New enquiry from the quote flow",
            "",
            f"Name: {enquiry.name}",
            f"Business: {enquiry.business}",
            f"Email: {enquiry.email}",
            f"Phone: {enquiry.phone}",
            f"Service: {enquiry.service or enquiry.scope_kind}",
            f"Scope: {enquiry.scope_size} {enquiry.addons}".strip(),
            f"Estimate: {enquiry.estimate}",
            f"Preferred slot: {enquiry.preferred_slot}",
            "",
            enquiry.message,
        ]
        EmailMessage(
            subject=f"Website quote enquiry from {enquiry.name or enquiry.email}",
            body="\n".join(lines),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.CONTACT_EMAIL],
            reply_to=[enquiry.email] if enquiry.email else None,
        ).send()
