from rest_framework import serializers
from core.models import Events, Category,Interest,Comment
from django.utils import timezone


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for category"""
    class Meta:
        model = Category
        fields = ['id', 'name']
        read_only_fields = ['id']


class EventsSerializer(serializers.ModelSerializer):
    """Serializer for events."""
    event_dates = serializers.DateField(format="%Y-%m-%d")  # Format the event date
    created_at = serializers.DateField(format="%Y-%m-%d")  # Format the created_at field
    time = serializers.TimeField(format='%H:%M:%S')  # Use TimeField to properly handle time format
    category = CategorySerializer(many=True)
    
    class Meta:
        model = Events
        fields = ['id', 'title', 'event_dates', 'link', 'created_at', 'time', 'category']
        read_only_fields = ['id']

    def _get_or_create_category(self, category, event):
        """Handle getting or creating category as needed."""
        auth_user = self.context['request'].user
        for category in category:
            category_obj, category = Category.objects.get_or_create(
                user=auth_user,
                **category,
            )
            event.category.add(category_obj)

    def create(self, validated_data):
        """Create an event."""
        categories = validated_data.pop('category', [])
        event = Events.objects.create(**validated_data)
        self._get_or_create_category(categories, event)
        return event

    def update(self, instance, validated_data):
        """Update event."""
        categories = validated_data.pop('category', None)
        if categories is not None:
            instance.category.clear()
            self._get_or_create_category(categories, instance)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance






class EventsDetailSerializer(EventsSerializer):
    """Serializer for event detail, including description."""
    class Meta(EventsSerializer.Meta):
        fields = EventsSerializer.Meta.fields + ['description']+['image']
        read_only_fields = ['image'] 

class EventsImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to events."""

    class Meta:
        model = Events
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': 'False'}}



class PublicEventsSerializer(serializers.ModelSerializer):
    """Serializer for public event listing."""
    event_dates = serializers.DateField(format="%Y-%m-%d")
    created_at = serializers.DateField(format="%Y-%m-%d")
    time = serializers.TimeField(format='%H:%M:%S')
    category = CategorySerializer(many=True)

    class Meta:
        model = Events
        fields = ['id', 'title', 'event_dates', 'link', 'created_at', 'time', 'category']
        read_only_fields = ['id']

class PublicEventsDetailSerializer (PublicEventsSerializer):

    class Meta(PublicEventsSerializer.Meta):
        fields = PublicEventsSerializer.Meta.fields + ['description']+['image']
        read_only_field = ['image']

class InterestSerializer(serializers.ModelSerializer):
    """Serializer for interests."""
    class Meta:
        model = Interest
        fields = ['id', 'user', 'event', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comments."""
    user = serializers.StringRelatedField(read_only=True)  # Show the user's name or email

    class Meta:
        model = Comment
        fields = ['id', 'user', 'event', 'text', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']