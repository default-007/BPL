from django.shortcuts import render
from django.views.generic import DetailView, ListView, View

from .models import Blog, Project, Service


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
