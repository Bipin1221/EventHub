from rest_framework import viewsets, mixins, status, generics,filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny,BasePermission
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .utils import send_ticket_email
from  core.models import Events
from core.models import Events, Category, Interest, Rating,Ticket
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
    CategorySerializer,
    TicketSerializer
)
import logging
logger = logging.getLogger(__name__)
from django.utils import timezone
from rest_framework.views import APIView
from io import BytesIO
from django_filters.rest_framework import DjangoFilterBackend


from .utils import send_ticket_email

from django.shortcuts import get_object_or_404

from .serializers import TicketSerializer


class IsOrganizer(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'organizer'

class EventsViewSet(viewsets.ModelViewSet):
    queryset = Events.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOrganizer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
   
    search_fields = ['title', 'description','category__name', 'venue_location'] 

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

# class CategoryViewSet(mixins.ListModelMixin,
#                      viewsets.GenericViewSet):
#     serializer_class = CategorySerializer
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated, IsOrganizer]
    
    # def get_queryset(self):
    #     return Category.objects.filter(user=self.request.user)

class PublicEventsListView(generics.ListAPIView):
    serializer_class = PublicEventsSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
   
    search_fields = ['title', 'description','category__name', 'venue_location'] 
    def get_queryset(self):
        return Events.objects.all()
    

class PublicCategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    queryset = Category.objects.all()

      
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
       
   
class TicketPurchaseAPIView(generics.CreateAPIView):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        event = get_object_or_404(Events, pk=self.kwargs['pk'])
        
        if self.request.user.role != 'attendee':
            raise PermissionDenied("Only attendees can purchase tickets.")

        try:
            ticket = serializer.save(user=self.request.user, event=event)
            send_ticket_email(ticket)
        except Exception as e:
            logger.error(f"Ticket purchase failed: {str(e)}")
            raise ValidationError("Ticket purchase failed. Please try again.")



class TicketValidationAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request, ticket_id):
        try:
            ticket = Ticket.objects.select_related('user', 'event').get(id=ticket_id)
            
            if request.user.role != 'organizer':
                raise PermissionDenied("Only organizers can validate tickets")

            if not ticket.event.user == request.user:
                raise PermissionDenied("You don't own this event")

            if ticket.validated_count >= ticket.quantity:
                return Response({"error": "All tickets in this purchase have been validated"}, status=status.HTTP_400_BAD_REQUEST)

            ticket.validated_count += 1
            ticket.save()

            validation_data = {
                "valid": True,
                "event": ticket.event.title,
                "ticket_type": ticket.ticket_type,
                "quantity": ticket.quantity,
                "validated_count": ticket.validated_count,
                "attendee": ticket.user.email,
                "purchased_at": ticket.purchased_at,
                "validation_time": timezone.now()
            }

            return Response(validation_data, status=status.HTTP_200_OK)

        except Ticket.DoesNotExist:
            return Response({"error": "Invalid ticket ID"}, status=status.HTTP_404_NOT_FOUND)
        
    # def get(self, request, ticket_id):
    #     ticket = get_object_or_404(Ticket, id=ticket_id)
        
    #     # Track how many times the ticket has been validated
    #     if ticket.validated_count < ticket.quantity:
    #         ticket.validated_count += 1
    #         ticket.save()
    #     else:
    #         return Response({"error": "All tickets validated"}, status=400)
        
    #     return Response({"validated_count": ticket.validated_count})
class UserTicketsAPIView(generics.ListAPIView):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    
    def get_queryset(self):
        if self.request.user.role == 'organizer':
            raise PermissionDenied(" organizers can't see the  tickets")
        
        else:
            return Ticket.objects.filter(user=self.request.user).select_related('event')