# events/tests/test_events.py
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Events, Category, Interest, Comment, Rating, Ticket, PaymentOrder
from Events.serializers import (
    EventCreateUpdateSerializer,
    EventListSerializer,
    CommentSerializer,
    RatingSerializer,
    InterestSerializer,
    TicketSerializer
)
from django.core.files.base import ContentFile
import uuid
import json
from unittest.mock import patch, Mock
from io import BytesIO
from reportlab.pdfgen import canvas

User = get_user_model()

class ModelTests(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            email='organizer@example.com',
            password='testpass123',
            role='organizer'
        )
        self.attendee = User.objects.create_user(
            email='attendee@example.com',
            password='testpass123',
            role='attendee'
        )
        self.category = Category.objects.create(name='Music')
        self.event = Events.objects.create(
            user=self.organizer,
            title='Test Event',
            description='Test Description',
            vip_price=100.00,
            common_price=50.00
        )
        self.event.category.add(self.category)

    def test_event_creation(self):
        self.assertEqual(self.event.title, 'Test Event')
        self.assertEqual(self.event.category.first().name, 'music')
        self.assertEqual(self.event.user.role, 'organizer')

    def test_ticket_creation(self):
        ticket = Ticket.objects.create(
            event=self.event,
            user=self.attendee,
            ticket_type='VIP'
        )
        self.assertTrue(ticket.qr_code.name.startswith('qr_'))
        self.assertEqual(ticket.validated_count, 0)

    def test_payment_order_creation(self):
        order = PaymentOrder.objects.create(
            user=self.attendee,
            event=self.event,
            ticket_type='vip',
            quantity=2,
            total_amount=200.00
        )
        self.assertEqual(order.status, 'initiated')

class SerializerTests(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            email='organizer@example.com',
            password='testpass123',
            role='organizer'
        )
        self.category = Category.objects.create(name='Tech')

    def test_event_serializer(self):
        data = {
            'title': 'New Event',
            'description': 'New Description',
            'category': ['Tech'],
            'vip_price': 150.00,
            'common_price': 75.00,
            'event_dates': '2024-01-01',
            'time_start': '10:00:00'
        }
        serializer = EventCreateUpdateSerializer(
            data=data,
            context={'request': Mock(user=self.organizer)}
        )
        self.assertTrue(serializer.is_valid())
        event = serializer.save()
        self.assertEqual(event.category.count(), 1)

class ViewTests(APITestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            email='organizer@example.com',
            password='testpass123',
            role='organizer'
        )
        self.attendee = User.objects.create_user(
            email='attendee@example.com',
            password='testpass123',
            role='attendee'
        )
        self.category = Category.objects.create(name='Music')
        self.event = Events.objects.create(
            user=self.organizer,
            title='Test Event',
            vip_price=100.00,
            common_price=50.00
        )
        self.client = APIClient()

    def test_event_crud(self):
        self.client.force_authenticate(user=self.organizer)
        # Create
        response = self.client.post(reverse('events-list'), {
            'title': 'New Event',
            'vip_price': 150.00,
            'common_price': 75.00,
            'category': ['Music'],
            'event_dates': '2024-01-01',
            'time_start': '10:00:00'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Update
        event_id = response.data['id']
        response = self.client.patch(
            reverse('events-detail', args=[event_id]),
            {'title': 'Updated Title'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_public_views(self):
        response = self.client.get(reverse('public-events-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

class EngagementTests(APITestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            email='organizer@example.com',
            password='testpass123',
            role='organizer'
        )
        self.attendee = User.objects.create_user(
            email='attendee@example.com',
            password='testpass123',
            role='attendee'
        )
        self.event = Events.objects.create(user=self.organizer, title='Test Event')
        self.client.force_authenticate(user=self.attendee)

    def test_comment_creation(self):
        response = self.client.post(
            reverse('create-comment', args=[self.event.id]),
            {'text': 'Great event!'}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_duplicate_rating(self):
        Rating.objects.create(user=self.attendee, event=self.event, value=5)
        response = self.client.post(
            reverse('create-rating', args=[self.event.id]),
            {'value': 4}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class PaymentTests(APITestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            email='organizer@example.com',
            password='testpass123',
            role='organizer'
        )
        self.attendee = User.objects.create_user(
            email='attendee@example.com',
            password='testpass123',
            role='attendee'
        )
        self.event = Events.objects.create(
            user=self.organizer,
            title='Paid Event',
            vip_price=150.00
        )
        self.client.force_authenticate(user=self.attendee)

    @patch('requests.post')
    def test_payment_flow(self, mock_post):
        mock_post.side_effect = [
            Mock(status_code=200, json=lambda: {'payment_url': 'test', 'pidx': 'test123'}),
            Mock(status_code=200, json=lambda: {'status': 'Completed'})
        ]
        
        # Initiate payment
        response = self.client.post(
            reverse('khalti-initiate', args=[self.event.id]),
            {'ticket_type': 'vip', 'quantity': 2}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Simulate callback
        response = self.client.get(reverse('khalti_payment_callback') + '?pidx=test123')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Ticket.objects.count(), 2)

class TicketTests(APITestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            email='organizer@example.com',
            password='testpass123',
            role='organizer'
        )
        self.attendee = User.objects.create_user(
            email='attendee@example.com',
            password='testpass123',
            role='attendee'
        )
        self.event = Events.objects.create(user=self.organizer, title='Test Event')
        self.ticket = Ticket.objects.create(
            event=self.event,
            user=self.attendee
        )

    def test_ticket_validation(self):
        self.client.force_authenticate(user=self.organizer)
        url = reverse('validate-ticket', args=[self.ticket.id])
        
        # First validation
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Second attempt
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class UtilTests(TestCase):
    @patch('Events.utils.EmailMessage')
    def test_email_sending(self, mock_email):
        from Events.utils import send_ticket_email
        user = User.objects.create(email='test@example.com')
        event = Events.objects.create(user=user, title='Test Event')
        ticket = Ticket.objects.create(event=event, user=user)
        
        send_ticket_email([ticket])
        mock_email.return_value.send.assert_called_once()

    def test_pdf_generation(self):
        from Events.utils import generate_ticket_pdf
        user = User.objects.create(email='test@example.com')
        event = Events.objects.create(user=user, title='Test Event')
        ticket = Ticket.objects.create(event=event, user=user)
        
        pdf = generate_ticket_pdf([ticket])
        self.assertTrue(len(pdf) > 1000)  # Basic PDF check

class PermissionTests(APITestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            email='organizer@example.com',
            password='testpass123',
            role='organizer'
        )
        self.attendee = User.objects.create_user(
            email='attendee@example.com',
            password='testpass123',
            role='attendee'
        )

    def test_role_permissions(self):
        # Attendee can't create event
        self.client.force_authenticate(user=self.attendee)
        response = self.client.post(reverse('events-list'), {'title': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)