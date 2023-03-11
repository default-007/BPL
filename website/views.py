from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView, DetailView, View, CreateView
from django.http import HttpResponse, HttpResponseRedirect
from taggit.models import Tag
from .models import *


class HomeView(View):
    #common_tags = Post.tags.most_common()[:4]

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
