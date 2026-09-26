import logging

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import DetailView, ListView, View

from .forms import ContactForm
from .models import Blog, Project, Service

logger = logging.getLogger(__name__)


class HomeView(View):
    def get(self, request):
        services = Service.objects.all()
        projects = Project.objects.all()
        blogs = Blog.objects.all()
        template_name = "home.html"
        context = {'services': services, 'projects': projects, 'blogs': blogs}
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
