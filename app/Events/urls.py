"""urls mapping for the event app"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from Events import views
from venueandsession.views import *
from rest_framework_nested import routers

router = routers.DefaultRouter()
router.register(r'events', views.EventsViewSet, basename='events')
# router.register('',views.CategoryViewSet)

#venue router
venue_router =routers.NestedDefaultRouter(router, r'events', lookup='event')
venue_router.register(r'venues', VenueViewSet, basename="event-venues" )

#Event Sessions router
events_sessions_router = routers.NestedDefaultRouter(router, r'events', lookup='event')
events_sessions_router.register(r'sessions', EventSessionViewSet, basename='event-sessions')


app_name = 'Events'
urlpatterns = [
    path('', include(router.urls)),
    path('', include(venue_router.urls)), #venue router
     path('', include(events_sessions_router.urls)), #session router
]
