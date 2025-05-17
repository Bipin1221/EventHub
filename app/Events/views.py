from rest_framework import viewsets, status, generics,filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny,BasePermission
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from django.db.models import Count
from .utils import send_ticket_email
from  core.models import Events,Ticket,PaymentOrder
from django.conf import settings
import requests
import json

from django.http import HttpResponseRedirect
from core.models import Events, Category, Interest, Rating, Ticket, Notification
from .serializers import (
    EventCreateUpdateSerializer,
    EventListSerializer,
    EventDetailSerializer,
    PublicEventsSerializer,
    PublicEventsDetailSerializer,
    CommentSerializer,
    RatingSerializer,
    InterestSerializer,
    NotificationSerializer,
    CategorySerializer,
    TicketSerializer,
    KhaltiInitiateSerializer,
    TicketStatsSerializer,
    
)
from .filters import EventFilter
from django.urls import reverse
import logging
logger = logging.getLogger(__name__)
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend


from .utils import send_ticket_email

from django.shortcuts import get_object_or_404

from .serializers import TicketSerializer


class IsOrganizer(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'organizer'



# from rest_framework.parsers import MultiPartParser, FormParser

class EventsViewSet(viewsets.ModelViewSet):
    # parser_classes = (MultiPartParser, FormParser)
    queryset = Events.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOrganizer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = EventFilter  # 👈 ADD THIS

    search_fields = ['title','category__name', 'venue_location'] 

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
# class EventImageUploadAPIView(generics.GenericAPIView):
#     permission_classes = [IsAuthenticated]
#     authentication_classes = [TokenAuthentication]
#     serializer_class = EventImageSerializer
#     def post(self, request, pk=None):
#         event = get_object_or_404(Events, pk=pk)  # Get the event instance

       
#         if self.request.user.role != 'organizer':
#             raise PermissionDenied("Only organizer can upload images")

#         # Check if the image is in the request files
#         if 'image' not in request.FILES:
#             raise ValidationError("No image provided")

#         # Save the image to the event
#         event.image = request.FILES['image']
#         event.save()

#         # Return the image URL in the response
#         return Response({'image_url': event.image.url}, status=status.HTTP_200_OK)

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
    filterset_class = EventFilter
    search_fields = ['title','category__name', 'venue_location'] 
    def get_queryset(self):
        return Events.objects.annotate(interest_count = Count('interests')).order_by('-interest_count','-created_at')
    

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


class InterestToggleAPIView(generics.GenericAPIView):
    serializer_class = InterestSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        event = get_object_or_404(Events, pk=pk)
        user = request.user

        # Check if user is attendee, optional but recommended
        if user.role != 'attendee':
            return Response({
                'interested': False,
                'interest_count': event.interests.count()
            }, status=status.HTTP_200_OK)

        interest_exists = Interest.objects.filter(user=user, event=event).exists()

        return Response({
            'interested': interest_exists,
            'interest_count': event.interests.count()
        }, status=status.HTTP_200_OK)

    def post(self, request, pk=None):
        event = get_object_or_404(Events, pk=pk)
        user = request.user

        if user.role != 'attendee':
            raise PermissionDenied("Only attendees can show interest")

        interest = Interest.objects.filter(user=user, event=event).first()

        if interest:
            # Interest exists — toggle off by deleting
            interest.delete()
            return Response({
                'interested': False,
                'interest_count': event.interests.count()
            }, status=status.HTTP_200_OK)

        # Interest does not exist — create new
        serializer = self.get_serializer(data={})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user, event=event)

        return Response({
            'interested': True,
            'interest_count': event.interests.count()
        }, status=status.HTTP_201_CREATED)
    

class ListEventInterest(generics.ListAPIView):
    serializer_class = PublicEventsDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Events.objects.filter(interests__user=self.request.user)

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes= [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        return Notification.objects.filter(recipient = user).order_by('-created_at')
    
class MarkNotificationReadView(generics.UpdateAPIView):
    """Mark a notification as read."""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        notification_id = kwargs.get('pk')
        try:
            notification = Notification.objects.get(id=notification_id, recipient=request.user)
            notification.is_read = True
            notification.save()
            return Response({'message': 'Notification marked as read.'}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found or unauthorized.'}, status=status.HTTP_404_NOT_FOUND)

# class TicketPurchaseAPIView(generics.CreateAPIView):
#     serializer_class = TicketSerializer
#     permission_classes = [IsAuthenticated]

#     def perform_create(self, serializer):
#         event = get_object_or_404(Events, pk=self.kwargs['pk'])
#         quantity = serializer.validated_data.get('quantity', 1)
#         x = serializer.validated_data.get('ticket_type')
#         if x== 'vip' or x== 'VIP' :
#             amt_sng = event.vip_price
#         else:
#             amt_sng = event.common_price

          
#         amt_sng=amt_sng*quantity
#         print(amt_sng)
#         user = self.request.user
       
#         # Role check
#         if user.role != 'attendee':
#             raise PermissionDenied(detail="Only attendees can purchase tickets.")
#         id = event.id
#         khalti_url = "http://127.0.0.1:8000/api/khalti/initiate/"
#         ticket_payload = {
#                             "id": id,
#                             "amount":float(amt_sng)
                            
#                                 }
#         ticket_response = requests.post(url=khalti_url, json=ticket_payload)
#         # Purchase limits
#         if ticket_response.status_code == 200:
#             tickets = []
#             for _ in range(quantity):
#                 ticket = Ticket.objects.create(
#                     user=user,
#                     event=event,
#                     ticket_type=serializer.validated_data['ticket_type'],
#                     quantity=1  # Each ticket represents 1 entry
#                 )
#                 tickets.append(ticket)

#             send_ticket_email(tickets)
        
#             logger.info(f"Ticket {ticket.id} created for {user.email}")
#         else:
#             return Response({"error": "Payment verification failed. Please contact support."}, status=status.HTTP_400_BAD_REQUEST)    

class TicketValidationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, id=ticket_id)
        organizer = request.user
        
        # Role check
        if organizer.role != 'organizer':
            raise PermissionDenied(detail="Only organizers can validate tickets.")
        
        # Ownership check
        if ticket.event.user != organizer:
            raise PermissionDenied(detail="You don't have permission to validate this ticket.")
        
        # Validation check
        
            
        if ticket.validated_count >= 1:
            return Response(
                {"error": "Ticket already validated."},
                status=status.HTTP_409_CONFLICT
            )
        
        # Validate ticket
        ticket.validated_count = 1
        ticket.save()
        
        return Response(
            {
                "status": "validated",
                "ticket_id": str(ticket.id),
                "event": ticket.event.title,
                "attendee": ticket.user.email,
                #"ticeket_used": ticket.delete()
            },
            status=status.HTTP_200_OK
            
        
        )
       
        

class UserTicketsAPIView(generics.ListAPIView):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role != 'attendee':
            raise PermissionDenied(detail="Only attendees can view their tickets.")
        return Ticket.objects.filter(user=user).select_related('event').order_by('-created_at')
    

class KhaltiInitiatePaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = KhaltiInitiateSerializer

    def post(self, request, pk):
        # Verify user role
        if request.user.role != 'attendee':
            return Response({"error": "Only attendees can purchase tickets"}, 
                          status=status.HTTP_403_FORBIDDEN)

        # Validate input
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            event = Events.objects.get(pk=pk)
            ticket_type = serializer.validated_data['ticket_type']
            quantity = serializer.validated_data['quantity']

            # Validate ticket type availability
            price_field = f'{ticket_type}_price'
            price = getattr(event, price_field, None)
            
            if not price:
                return Response({"error": f"{ticket_type.title()} tickets not available for this event"},
                              status=status.HTTP_400_BAD_REQUEST)

            # Calculate total amount
            total_amount = price * quantity

            # Create payment order
            payment_order = PaymentOrder.objects.create(
                user=request.user,
                event=event,
                ticket_type=ticket_type,
                quantity=quantity,
                total_amount=total_amount,
                status='initiated'
            )

            # Prepare Khalti payload
            payload = {
                "return_url": request.build_absolute_uri(reverse("khalti_payment_callback")),
                "website_url": "http://localhost:5173",
                "amount": int(total_amount * 100),  # Convert to paisa
                "purchase_order_id": str(payment_order.id),
                "purchase_order_name": f"Ticket-{payment_order.id}",
                "merchant_username": "Event Ticketing",
            }

            headers = {
                "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
                "Content-Type": "application/json"
            }

            # Initiate payment
            response = requests.post(settings.KHALTI_INITIATE_URL, json=payload, headers=headers)
            response.raise_for_status()
            khalti_data = response.json()

            # Update payment order
            payment_order.pidx = khalti_data['pidx']
            payment_order.save()

            return Response({"payment_url": khalti_data['payment_url'],
                             "auto_redirect":True
                             }, 
                          status=status.HTTP_200_OK)

        except Events.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Payment initiation error: {str(e)}")
            return Response({"error": "Payment processing failed"}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)








logger = logging.getLogger(__name__)

class KhaltiPaymentCallbackView(APIView):
    def get(self, request):
        pidx = request.GET.get("pidx")
        transaction_id = request.GET.get("transaction_id")

        logger.info(f"Payment callback received - pidx: {pidx}, transaction_id: {transaction_id}")

        if not pidx:
            logger.error("Missing pidx parameter in callback")
            return Response({
                "status": "error",
                "message": "Missing payment reference ID"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            headers = {"Authorization": f"Key {settings.KHALTI_SECRET_KEY}"}
            verify_response = requests.post(
                "https://a.khalti.com/api/v2/epayment/lookup/",
                json={"pidx": pidx},
                headers=headers,
                timeout=10
            )

            verify_response.raise_for_status()
            verify_data = verify_response.json()

            logger.info(f"Khalti verification response: {json.dumps(verify_data, indent=2)}")

            if verify_data.get("status") == "Completed":
                try:
                    payment_order = PaymentOrder.objects.get(pidx=pidx, status='initiated')
                except PaymentOrder.DoesNotExist:
                    logger.error(f"PaymentOrder not found for pidx: {pidx}")
                    return Response({
                        "status": "error",
                        "message": "Invalid transaction reference"
                    }, status=status.HTTP_400_BAD_REQUEST)

                try:
                    tickets = [
                        Ticket.objects.create(
                            user=payment_order.user,
                            event=payment_order.event,
                            ticket_type=payment_order.ticket_type,
                            quantity=1
                        ) for _ in range(payment_order.quantity)
                    ]
                    logger.info(f"Created {len(tickets)} tickets")
                except Exception as e:
                    logger.error(f"Ticket creation failed: {str(e)}")
                    return Response({
                        "status": "error",
                        "message": "Ticket generation failed"
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                try:
                    send_ticket_email(tickets)
                    logger.info(f"Sent ticket email to {payment_order.user.email}")
                except Exception as e:
                    logger.error(f"Email sending failed: {str(e)}")
                    return Response({
                        "status": "error",
                        "message": "Ticket delivery failed"
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                payment_order.status = 'completed'
                payment_order.transaction_id = transaction_id or verify_data.get("transaction_id", "")
                payment_order.save()
                logger.info(f"Updated payment order {payment_order.id} to completed")

                return HttpResponseRedirect("http://localhost:5173/attendee-dashboard/book-event")

            logger.warning(f"Payment not completed. Status: {verify_data.get('status')}")
            return Response({
                "status": "error",
                "message": f"Payment status: {verify_data.get('status')}"
            }, status=status.HTTP_400_BAD_REQUEST)

        except requests.exceptions.RequestException as e:
            logger.error(f"Khalti API connection error: {str(e)}")
            return Response({
                "status": "error",
                "message": "Payment gateway communication failed"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid Khalti response format: {str(e)}")
            return Response({
                "status": "error",
                "message": "Invalid payment gateway response"
            }, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return Response({
                "status": "error",
                "message": "Payment processing failed"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




# Use your actual permission class

class TicketStatsView(APIView):
    permission_classes = [IsAuthenticated, IsOrganizer]

    def get(self, request, event_id):
        try:
            event = Events.objects.get(pk=event_id, user=request.user)
        except Events.DoesNotExist:
            return Response({'error': 'Event not found or unauthorized.'}, status=status.HTTP_404_NOT_FOUND)

        stats_data = TicketStatsSerializer.get_stats(event)
        serializer = TicketStatsSerializer(stats_data)
        return Response(serializer.data)




