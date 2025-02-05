"""urls mapping for the event app"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from Events import views

router = DefaultRouter()
router.register('', views.EventsViewSet)
router.register('category',views.CategoryViewSet)
app_name = 'Events'
urlpatterns = [
    path('', include(router.urls)),
]
