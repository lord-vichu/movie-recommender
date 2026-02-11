"""
URL configuration for movie_recommender project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),  # Allauth URLs for social auth
    path('', include('movies.urls')),
]
