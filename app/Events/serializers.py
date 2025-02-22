from rest_framework import serializers
from core.models import Events, Category, Interest, Comment, Rating, EventImage, Ticket

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']
        read_only_fields = ['id']

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['id', 'ticket_type', 'ticket_price', 'available_quantity']
        read_only_field=['id']


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    category = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        write_only=True
    )
    ticket= TicketSerializer(many=True, required=False)
    event_dates = serializers.DateField(format="%Y-%m-%d")
    time_start = serializers.TimeField(format='%H:%M:%S')

    class Meta:
        model = Events
        fields = ['id', 'title', 'event_dates', 'time_start',
                  'venue_name', 'venue_location', 'venue_capacity', 
                  'link', 'description', 'category', 'ticket',
                  ]
        read_only_fields = ['id']

    def create(self, validated_data):
        categories = validated_data.pop('category', [])
        ticket_datas = validated_data.pop('ticket',[])
        event = Events.objects.create(
            user=self.context['request'].user,
            **validated_data
        )
        for ticket_data in ticket_datas:
            Ticket.objects.create(event=event, **ticket_data)
        
        self._handle_categories(categories, event)
        return event

    def update(self, instance, validated_data):
        category_names = validated_data.pop('category', None)
        if category_names is not None:
            instance.category.clear()
            self._handle_categories(category_names, instance)
        return super().update(instance, validated_data)

    def _handle_categories(self, category_names, event):
        for name in category_names:
            normalized_name = name.strip().lower()
            cat, _ = Category.objects.get_or_create(name=normalized_name)
            event.category.add(cat)


class EventListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(many=True)
    event_dates = serializers.DateField(format="%Y-%m-%d")
    time_start = serializers.TimeField(format='%H:%M:%S')
    interest_count = serializers.SerializerMethodField()

    class Meta:
        model = Events
        fields = ['id', 'title', 'event_dates', 
                  'time_start', 'link', 'category','interest_count']
        
    def get_interest_count(self ,obj):
            return obj.interests.count()

class EventDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(many=True)
    comments = serializers.SerializerMethodField()
    ratings = serializers.SerializerMethodField()
    event_dates = serializers.DateField(format="%Y-%m-%d")
    time_start = serializers.TimeField(format='%H:%M:%S')
    user = serializers.StringRelatedField(read_only=True)
    ticket= TicketSerializer(many=True, required=False)
    interest_count = serializers.SerializerMethodField()
    class Meta:
        model = Events
        fields = [
            'id', 'title', 'event_dates', 'time_start',
             'venue_name', 'venue_location', 'venue_capacity','link', 
            'description', 'image', 'category',
              'comments', 'ratings', 'user', 'ticket','interest_count'
        ]

    def get_comments(self, obj):
        return CommentSerializer(obj.comments.all(), many=True).data

    def get_ratings(self, obj):
        return RatingSerializer(obj.ratings.all(), many=True).data
   
    def get_interest_count(self ,obj):
        return obj.interests.count()

class PublicEventsSerializer(EventListSerializer):
    created_at = serializers.DateField(format="%Y-%m-%d")
    
    class Meta(EventListSerializer.Meta):
        fields = EventListSerializer.Meta.fields + ['created_at']

class PublicEventsDetailSerializer(EventDetailSerializer):
    created_at = serializers.DateField(format="%Y-%m-%d")
    
    class Meta(EventDetailSerializer.Meta):
        fields = EventDetailSerializer.Meta.fields + ['created_at']

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'user', 'text', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class RatingSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Rating
        fields = ['id', 'user', 'value', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ['id', 'user', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class EventImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventImage
        fields = ['id', 'image', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class KhaltiInitiateSerializer(serializers.Serializer):
    event_id = serializers.IntegerField(required=True)
    class Meta:
        fields = ['event_id']


# class KhaltiVerifySerializer(serializers.Serializer):
#     token = serializers.CharField()
#     amount = serializers.CharField()
#     class Meta:
#         fields = ['token', 'amount']