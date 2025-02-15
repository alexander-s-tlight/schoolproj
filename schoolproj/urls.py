from django.contrib import admin, auth
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path("accounts/", include('django.contrib.auth.urls')),
    path('', include('tasks.urls')),
]