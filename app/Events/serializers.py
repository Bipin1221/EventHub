from rest_framework import serializers
from core.models import Events, Category, Interest, Comment, Rating, Ticket, Notification
from rest_framework.exceptions import ValidationError

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']
        read_only_fields = ['id']


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    category = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        write_only=True
    )
    event_dates = serializers.DateField(format="%Y-%m-%d")
    time_start = serializers.TimeField(format='%H:%M:%S')
    user = serializers.StringRelatedField()
    image = serializers.ImageField(required = False)
    interest_count = serializers.SerializerMethodField()
    class Meta:
        model = Events
        fields = ['id', 'title', 'event_dates', 'time_start',
                  'venue_name', 'venue_location', 'venue_capacity', 
                   'description', 'category','vip_price','common_price','user','image','interest_count'
                  ]
        read_only_fields = ['id']

    def create(self, validated_data):
        category_names = validated_data.pop('category', [])
        event = Events.objects.create(
            user=self.context['request'].user,
            **validated_data
        )
        self._handle_categories(category_names, event)
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
    
    def get_interest_count(self, obj):
        return obj.interests.count()

class EventListSerializer(serializers.ModelSerializer):
    # category = CategorySerializer(many=True)
    # event_dates = serializers.DateField(format="%Y-%m-%d")
    # time_start = serializers.TimeField(format='%H:%M:%S')
    # interest_count = serializers.SerializerMethodField()
    # image = serializers.ImageField(required = False)
    # class Meta:
    #     model = Events
    #     fields = ['id', 'title', 'event_dates', 'time_start', 'category','image','interest_count']

    # def get_interest_count(self, obj):
    #     return obj.interests.count()
    category = CategorySerializer(many=True)
    comments = serializers.SerializerMethodField()
    interested_count = serializers.SerializerMethodField()
    ratings = serializers.SerializerMethodField()
    event_dates = serializers.DateField(format="%Y-%m-%d")
    time_start = serializers.TimeField(format='%H:%M:%S')
    organizer_name = serializers.CharField(source='user.name', read_only=True)
    vip_price = serializers.DecimalField(max_digits=10,decimal_places=2,required = False)
    common_price = serializers.DecimalField(max_digits=10,decimal_places=2,required = False)
    user= serializers.SerializerMethodField()
    class Meta:
        model = Events
        fields = [
            'id', 'title', 'event_dates', 'time_start',
             'venue_name', 'venue_location', 'venue_capacity', 
            'description','organizer_name', 'image', 'category',
              'comments', 'ratings','vip_price','common_price','interested_count','user',
        ]

    def get_comments(self, obj):
        return CommentSerializer(obj.comments.all(), many=True).data

    def get_user(self, obj):
        return obj.user.email
    def get_ratings(self, obj):
        return RatingSerializer(obj.ratings.all(), many=True).data
    def get_interested_count(self, obj):
        return obj.interests.count()
class EventDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(many=True)
    comments = serializers.SerializerMethodField()
    interested_count = serializers.SerializerMethodField()
    ratings = serializers.SerializerMethodField()
    event_dates = serializers.DateField(format="%Y-%m-%d")
    time_start = serializers.TimeField(format='%H:%M:%S')
    organizer_name = serializers.CharField(source ='user.name', read_only=True)
    vip_price = serializers.DecimalField(max_digits=10,decimal_places=2,required = False)
    common_price = serializers.DecimalField(max_digits=10,decimal_places=2,required = False)
    user= serializers.SerializerMethodField()
    class Meta:
        model = Events
        fields = [
            'id', 'title', 'event_dates', 'time_start',
             'venue_name', 'venue_location', 'venue_capacity', 
            'description', 'image', 'category',
              'comments', 'ratings', 'organizer_name','vip_price','common_price','interested_count','user'
        ]
    

    def get_user(self, obj):
        return obj.user.email

    def get_comments(self, obj):
        return CommentSerializer(obj.comments.all(), many=True).data

    def get_ratings(self, obj):
        return RatingSerializer(obj.ratings.all(), many=True).data
    def get_interested_count(self, obj):
        return obj.interests.count()

class PublicEventsSerializer(EventListSerializer):
    
    
    class Meta(EventListSerializer.Meta):
        fields = EventListSerializer.Meta.fields
        

class PublicEventsDetailSerializer(EventDetailSerializer):
   
    
    class Meta(EventDetailSerializer.Meta):
        fields = EventDetailSerializer.Meta.fields 

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

# class EventImageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = EventImage
#         fields = ['id', 'image', 'uploaded_at']
#         read_only_fields = ['id', 'uploaded_at']


class TicketSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    user_email = serializers.SerializerMethodField(read_only=True)
    quantity = serializers.IntegerField(default = 1)
    event_dates = serializers.CharField(source='event.event_dates', read_only=True)
    time_start = serializers.CharField(source='event.time_start', read_only=True)
    venue_location = serializers.CharField(source='event.venue_location', read_only=True)
    venue_name = serializers.CharField(source='event.venue_name', read_only=True)
    

    class Meta:
        model = Ticket
        fields = [
            'id', 'event_title', 'user_email', 
            'ticket_type', 'qr_code', 'quantity','event_dates','time_start','venue_location', 'venue_name',
        ]
        read_only_fields = ['id', 'qr_code']
        write_only_fields = ['quantity']

    def get_user_email(self, obj):
        return obj.user.email


class KhaltiInitiateSerializer(serializers.Serializer):
    ticket_type = serializers.ChoiceField(choices=[('vip', 'VIP'), ('common', 'Common')])
    quantity = serializers.IntegerField(min_value=1)
    class Meta:
        fields = ['id','ticket_type', 'quantity']
        read_only_fields = ['id']





class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'event', 'message', 'is_read', 'created_at']
        read_only_fields = ['id', 'recipient', 'event', 'message', 'created_at']



from rest_framework import serializers
from core.models import Ticket,Events

from django.db.models import Sum

class TicketStatsSerializer(serializers.Serializer):
    event_id = serializers.IntegerField()
    event_title = serializers.CharField()
    venue_capacity = serializers.IntegerField()
    vip_tickets_sold = serializers.IntegerField()
    common_tickets_sold = serializers.IntegerField()
    total_tickets_sold = serializers.IntegerField()
    remaining_tickets = serializers.IntegerField()
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)

    @staticmethod
    def get_stats(event):
        tickets = Ticket.objects.filter(event=event)
        vip_sold = tickets.filter(ticket_type__iexact='VIP').aggregate(total=Sum('quantity'))['total'] or 0
        common_sold = tickets.filter(ticket_type__iexact='COMMON').aggregate(total=Sum('quantity'))['total'] or 0

        total_sold = vip_sold + common_sold
        remaining = max(event.venue_capacity - total_sold, 0)
        total_price = (vip_sold * event.vip_price) + (common_sold * event.common_price)
        return {
            'event_id': event.id,
            'event_title': event.title,
            'venue_capacity': event.venue_capacity,
            'vip_tickets_sold': vip_sold,
            'common_tickets_sold': common_sold,
            'total_tickets_sold': total_sold,
            'remaining_tickets': remaining,
            'total_price': total_price

        }
