from rest_framework import serializers
from core.models import Venue
from core.models import EventSession

class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = ['id','name','address', 'capacity']
        # extra_kwargs = {
        #     'event': {'required': True}
        # }

class EventSessionSerializer(serializers.ModelSerializer):
    event_id = serializers.ReadOnlyField()
    class Meta:
        model = EventSession
        fields = ['id','start_time','end_time', 'available_seats', 'event_id']
        # extra_kwargs = {
        #     'event': {'required': True},
        #     'venue': {'required': True}
        # }
        # def create(self, validated_data):
        #     event_id= self.context["event_id"]
            
        #     return EventSession.objects.create(event_id= event_id, **validated_data)
