"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings
from drf_spectacular.views import (

SpectacularAPIView,
SpectacularSwaggerView
)
from Events.views import KhaltiInitiatePaymentAPIView, KhaltiVerifyAPIView



urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('api/schema/',SpectacularAPIView.as_view(),name='api-schema'),
    path('api/docs/',SpectacularSwaggerView.as_view(url_name='api-schema'),name='api-docs'),
    path('api/user/', include('user.urls', namespace='user')),
    path('api/events/',include('Events.urls')),
]
urlpatterns+= [
    path('api/khalti/initiate/', KhaltiInitiatePaymentAPIView.as_view(), name='khalti_initiate_payment'),
    path('api/khalti/verify/', KhaltiVerifyAPIView.as_view(), name='khalti_verify_payment'),
  #  path('khalti/callback/', KhaltiPaymentCallbackAPIView.as_view(), name='khalti_payment_callback'), # Implement this in django style
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,

    )
