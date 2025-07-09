from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('login'), name='home'),  # Redirect root to login
    path('', include('core.urls')),  # Include core URLs first
    path('admin/', admin.site.urls),  # Admin URLs after core
]