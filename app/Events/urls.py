"""urls mapping for the event app"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from Events import views

router = DefaultRouter()
router.register('', views.EventsViewSet)
router.register('category',views.CategoryViewSet)
app_name = 'events'

   

urlpatterns = [

    path('show-events/', views.PublicEventsListView.as_view(), name='public-list'),
    path('show-event/<int:pk>/', views.PublicEventsDetailView.as_view(), name='public-events-detail'),
    path('<int:pk>/show-interest/', views.EventsViewSet.as_view({'post': 'show_interest'}), name='show-interest'),
    path('<int:pk>/add-comment/', views.EventsViewSet.as_view({'post': 'add_comment'}), name='add-comment'),
    path('<int:pk>/rate-event/', views.EventsViewSet.as_view({'post': 'rate_event'}), name='rate-event'),
    path('<int:pk>/upload-images/', views.EventsViewSet.as_view({'post': 'upload_images'}), name='upload-images'),
    path('', include(router.urls)),
]
