
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

# Create your views here.
from rest_framework import viewsets
from core.models import Venue, EventSession, Events
from .serializers import VenueSerializer, EventSessionSerializer
from .custom_permission import IsEventOwner
from rest_framework import serializers

class VenueViewSet(viewsets.ModelViewSet):

    serializer_class = VenueSerializer
    authentication_classes=[TokenAuthentication]
    permission_classes=[IsAuthenticated]

    def perform_create(self, serializer):
        # Automatically link the venue to the event from the URL
        event_id = self.kwargs['event_pk']
        event = Events.objects.get(id=event_id)
        serializer.save(event=event)

    def get_queryset(self):
        return Venue.objects.filter(event_id=self.kwargs['event_pk'])
    
    # def perform_create(self, serializer):
    #     # Ensure the session is created only for the current user's event
    #     event = Event.objects.filter(
    #         owner=self.request.user, 
    #         id=serializer.validated_data['event'].id
    #     ).first()
        
    #     if not event:
    #         raise serializers.ValidationError(
    #             "You can only create venues for your own events"
    #         )
        
    #     serializer.save()



class EventSessionViewSet(viewsets.ModelViewSet):
    queryset = EventSession.objects.all()
    serializer_class = EventSessionSerializer
    authentication_classes=[TokenAuthentication]
    permission_classes=[IsAuthenticated]

    def perform_create(self, serializer):
        # Automatically link the venue to the event from the URL
        event_id = self.kwargs['event_pk']
        event = Events.objects.get(id=event_id)
        serializer.save(event=event)
    
    def get_queryset(self):
        return EventSession.objects.filter(event_id=self.kwargs['event_pk'])
    

    # def perform_create(self, serializer):
    #     # Ensure the session is created only for the current user's event
    #     event = Event.objects.filter(
    #         owner=self.request.user, 
    #         id=serializer.validated_data['event_id'].id
    #     ).first()
        
    #     if not event:
    #         raise serializers.ValidationError(
    #             "You can only create sessions for your own events"
    #         )
        
    #     serializer.save()


