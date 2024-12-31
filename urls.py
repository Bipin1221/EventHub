from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),  # Home app
    path('accounts/', include('accounts.urls')),  # Accounts app
    path('posts/', include('posts.urls')),  # Posts app
]
