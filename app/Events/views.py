from rest_framework import viewsets, mixins, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny,BasePermission
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from django.db.models import Q
from  core.models import Events, Ticket
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
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
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
#                      mixins.UpdateModelMixin,
#                      mixins.DestroyModelMixin,
#                      viewsets.GenericViewSet):
#     serializer_class = CategorySerializer
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated, IsOrganizer]
    
#     def get_queryset(self):
#         return Category.objects.filter(user=self.request.user)

class PublicCategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    queryset = Category.objects.all()


class PublicEventsListView(generics.ListAPIView):
    serializer_class = PublicEventsSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
   
    search_fields = ['title', 'description','category__name', 'venue_location'] 
    def get_queryset(self):
        return Events.objects.all()
      
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
       
   

########
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.conf import settings
import requests
from rest_framework.permissions import AllowAny
import logging
 # Import your Events model
from .serializers import KhaltiInitiateSerializer, KhaltiVerifySerializer  # Import serializers

logger = logging.getLogger(__name__)

class KhaltiInitiatePaymentAPIView(APIView):
    """
    Initiates a Khalti payment for a given product.
    """
    permission_classes = [AllowAny] # or permission_classes = [IsAuthenticated]
    serializer_class = KhaltiInitiateSerializer

    def post(self, request):
        serializer = KhaltiInitiateSerializer(data=request.data)
        if serializer.is_valid():
            event_id = serializer.validated_data['event_id']
            try:
                event=get_object_or_404(Events, id=event_id)
                ticket = get_object_or_404(Ticket, event_id=event_id)  # Use Events model instead of Product
                amount = int(ticket.ticket_price * 100)  # Access the ticket_price and Convert NPR to paisa. Ensure Events has ticket_price

                payload = {
                    "return_url": request.build_absolute_uri(reverse("khalti_payment_callback")),
                    "website_url": "https://yourwebsite.com/",
                    "amount": amount,
                    "purchase_order_id": f"order_{event.id}",
                    "purchase_order_name": event.title,
                    "merchant_username": "Event Ticketing System",
                    "merchant_extra": "merchant_extra"  
                }

                headers = {
                    "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
                    "Content-Type": "application/json"
                }

                # Debugging: Print request data before sending it
                logger.info(f"Initiating Khalti Payment with: {payload}")
                logger.info(f"Using Secret Key: {settings.KHALTI_SECRET_KEY}")

                response = requests.post(settings.KHALTI_INITIATE_URL, json=payload, headers=headers)

                # Debugging: Print response
                logger.info(f"Khalti Response Status: {response.status_code}")
                logger.info(f"Khalti Response Data: {response.text}")

                if response.status_code == 200:
                    data = response.json()
                    return Response({"payment_url": data["payment_url"]}, status=status.HTTP_200_OK)  # Return the payment URL
                else:
                    return Response({"error": "Payment initiation failed", "details": response.text}, status=response.status_code)

            except Events.DoesNotExist:
                return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class KhaltiVerifyAPIView(APIView):
    """
    Verifies a Khalti payment.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = KhaltiVerifySerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            amount = serializer.validated_data['amount']

            headers = {
                "Authorization": f"Key {settings.KHALTI_SECRET_KEY}"
            }

            data = {
                "token": token,
                "amount": amount
            }

            response = requests.post(settings.KHALTI_VERIFY_URL, data=data, headers=headers)

            if response.status_code == 200:
                return Response({"status": "success", "message": "Payment verified!"}, status=status.HTTP_200_OK)
            else:
                return Response({"status": "failure", "message": "Verification failed", "details": response.json()}, status=response.status_code)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class KhaltiPaymentCallbackView(APIView):
    def get(self, request):
        logger = logging.getLogger(__name__)
        pidx = request.GET.get("pidx")
        amount = request.GET.get("amount")

        if not pidx or not amount:
            return Response({"error": "Invalid payment request. Missing pidx or amount."}, status=status.HTTP_400_BAD_REQUEST)

        headers = {"Authorization": f"Key {settings.KHALTI_SECRET_KEY}"}
        verify_url = "https://a.khalti.com/api/v2/epayment/lookup/"
        verify_payload = {"pidx": pidx}

        logger.info(f"Sending verification request to Khalti with: {verify_payload}")
        verify_response = requests.post(verify_url, json=verify_payload, headers=headers)

        if verify_response.status_code == 200:
            verify_data = verify_response.json()
            logger.info(f"Khalti Verification Response: {verify_data}")

            if verify_data.get("status") == "Completed":
                return Response({"message": "Payment Successful! Thank you for your purchase.",
                                "amt": amount}, status=status.HTTP_200_OK)

        return Response({"error": "Payment verification failed. Please contact support."}, status=status.HTTP_400_BAD_REQUEST)
