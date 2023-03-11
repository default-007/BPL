from django.conf.urls import url, include
from django.urls import path
from .views import *
from . import views

app_name = "website"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    # path('l/', LandingPage.as_view(), name='landing'),
    path("about/", AboutView.as_view(), name="about"),
    path("blog/", BlogView.as_view(), name="blog"),
    path("blog/<slug>/", BlogDetailView.as_view(), name="blog"),
    path("project/", ProjectListView.as_view(), name="project"),
    path("service/", ServiceListView.as_view(), name="service"),
    path("service/<slug>/", ServiceView.as_view(), name="service"),
    path("project/<slug>/", ProjectDetailView.as_view(), name="project"),
]
