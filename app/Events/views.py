from rest_framework import viewsets, mixins, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny,BasePermission
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from django.db.models import Q
from  core.models import Events
from core.models import Events, Category, Interest, Comment, Rating
from .serializers import (
    EventCreateUpdateSerializer,
    EventListSerializer,
    EventDetailSerializer,
    PublicEventsSerializer,
    PublicEventsDetailSerializer,
    CommentSerializer,
    RatingSerializer,
    InterestSerializer,
    EventImageSerializer,
    CategorySerializer
)

class IsOrganizer(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'organizer'

class EventsViewSet(viewsets.ModelViewSet):
    queryset = Events.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOrganizer]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EventCreateUpdateSerializer
        if self.action == 'list':
            return EventListSerializer
        return EventDetailSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)\
                   .prefetch_related('category')\
                   .order_by('-created_at')
class EventImageUploadAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    serializer_class = EventImageSerializer
    def post(self, request, pk=None):
        event = get_object_or_404(Events, pk=pk)  # Get the event instance

       
        if self.request.user.role != 'organizer':
            raise PermissionDenied("Only organizer can upload images")

        # Check if the image is in the request files
        if 'image' not in request.FILES:
            raise ValidationError("No image provided")

        # Save the image to the event
        event.image = request.FILES['image']
        event.save()

        # Return the image URL in the response
        return Response({'image_url': event.image.url}, status=status.HTTP_200_OK)

class CategoryViewSet(mixins.ListModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = CategorySerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOrganizer]
    
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

class PublicEventsListView(generics.ListAPIView):
    serializer_class = PublicEventsSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = Events.objects.all()
        category_ids = self.request.query_params.get('category')
        search = self.request.query_params.get('search')
        
        if category_ids:
            queryset = queryset.filter(category__id__in=category_ids.split(','))
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
        return queryset.order_by('-created_at')

class PublicEventsDetailView(generics.RetrieveAPIView):
    serializer_class = PublicEventsDetailSerializer
    permission_classes = [AllowAny]
    queryset = Events.objects.all()

class CommentCreateAPIView(generics.CreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        event = get_object_or_404(Events, pk=self.kwargs['pk'])
        if self.request.user.role != 'attendee':
            raise PermissionDenied("Only attendees can comment")
        serializer.save(user=self.request.user, event=event)

class RatingCreateAPIView(generics.CreateAPIView):
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        event = get_object_or_404(Events, pk=self.kwargs['pk'])
        if self.request.user.role != 'attendee':
            raise PermissionDenied("Only attendees can rate events")
        if Rating.objects.filter(user=self.request.user, event=event).exists():
            raise ValidationError("You've already rated this event")
        serializer.save(user=self.request.user, event=event)

class InterestCreateAPIView(generics.CreateAPIView):
    serializer_class = InterestSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        event = get_object_or_404(Events, pk=self.kwargs['pk'])
        if self.request.user.role != 'attendee':
            raise PermissionDenied("Only attendees can show interest")
        if Interest.objects.filter(user=self.request.user, event=event).exists():
            raise ValidationError("You've already shown interest")
        serializer.save(user=self.request.user, event=event)