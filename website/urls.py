from django.urls import path

from .views import (
    AboutView,
    BlogDetailView,
    BlogView,
    ContactView,
    HomeView,
    ProjectDetailView,
    ProjectListView,
    ServiceListView,
    ServiceView,
)

app_name = "website"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    # path('l/', LandingPage.as_view(), name='landing'),
    path("about/", AboutView.as_view(), name="about"),
    path("contact/", ContactView.as_view(), name="contact"),
    path("blog/", BlogView.as_view(), name="blog"),
    path("blog/<slug:slug>/", BlogDetailView.as_view(), name="blog_detail"),
    path("project/", ProjectListView.as_view(), name="project"),
    path("project/<slug:slug>/", ProjectDetailView.as_view(), name="project_detail"),
    path("service/", ServiceListView.as_view(), name="service"),
    path("service/<slug:slug>/", ServiceView.as_view(), name="service_detail"),
]
