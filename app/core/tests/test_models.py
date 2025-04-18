from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid
import os

from core.models import (
    Category,
    Events,
    Interest,
    Comment,
    Rating,
    Ticket,
    PaymentOrder
)

User = get_user_model()

class ModelTests(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User',
            role='attendee'
        )
        
        # Create test category
        self.category = Category.objects.create(name='Music')
        
        # Create test event
        self.event = Events.objects.create(
            user=self.user,
            title='Test Event',
            description='Test Description',
            vip_price=100.00,
            common_price=50.00,
            venue_name='Test Venue'
        )
        self.event.category.add(self.category)

    # User Model Tests
    def test_create_user_with_email_successful(self):
        """Test creating a user with an email is successful"""
        user = User.objects.create_user(
            email='test2@example.com',
            password='testpass123',
            name='Test User 2'
        )
        self.assertEqual(user.email, 'test2@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertEqual(user.role, 'attendee')

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users"""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com']
        ]
        for email, expected in sample_emails:
            user = User.objects.create_user(email, 'test123')
            self.assertEqual(user.email, expected)

    def test_create_superuser(self):
        """Test creating a superuser"""
        admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)

    # Category Model Tests
    def test_category_name_normalization(self):
        """Test category name is normalized to lowercase"""
        category = Category.objects.create(name='  ROCK MUSIC  ')
        self.assertEqual(category.name, 'rock music')

    def test_category_str_representation(self):
        """Test category string representation"""
        self.assertEqual(str(self.category), 'music')

    # Event Model Tests
    def test_event_creation(self):
        """Test event creation with required fields"""
        self.assertEqual(self.event.title, 'Test Event')
        self.assertEqual(self.event.venue_name, 'Test Venue')
        self.assertEqual(self.event.category.count(), 1)

    def test_event_image_upload_path(self):
        """Test event image is uploaded to correct path"""
        filename = 'test.jpg'
        mock_image = SimpleUploadedFile(
            name=filename,
            content=b'',
            content_type='image/jpeg'
        )
        event = Events.objects.create(
            user=self.user,
            title='Event with image',
            image=mock_image
        )
        self.assertTrue(os.path.dirname(event.image.path).endswith('uploads/events'))
        self.assertTrue(uuid.UUID(os.path.splitext(os.path.basename(event.image.name))[0]))

    # Interest Model Tests
    def test_interest_creation(self):
        """Test creating an interest relationship"""
        interest = Interest.objects.create(
            user=self.user,
            event=self.event
        )
        self.assertEqual(interest.event, self.event)
        self.assertEqual(interest.user, self.user)

    # Comment Model Tests
    def test_comment_creation(self):
        """Test creating a comment on an event"""
        comment = Comment.objects.create(
            user=self.user,
            event=self.event,
            text='Great event!'
        )
        self.assertEqual(comment.text, 'Great event!')

    # Rating Model Tests
    def test_rating_creation(self):
        """Test creating a rating for an event"""
        rating = Rating.objects.create(
            user=self.user,
            event=self.event,
            value=5
        )
        self.assertEqual(rating.value, 5)

    def test_rating_value_validation(self):
        """Test rating value validation"""
        with self.assertRaises(ValidationError):
            Rating.objects.create(
                user=self.user,
                event=self.event,
                value=6
            ).full_clean()

    # Ticket Model Tests
    def test_ticket_creation(self):
        """Test ticket creation with QR code generation"""
        ticket = Ticket.objects.create(
            event=self.event,
            user=self.user,
            ticket_type='VIP'
        )
        self.assertTrue(ticket.qr_code)
        self.assertEqual(ticket.ticket_type, 'VIP')

    # PaymentOrder Model Tests
    def test_payment_order_creation(self):
        """Test payment order creation"""
        payment_order = PaymentOrder.objects.create(
            user=self.user,
            event=self.event,
            ticket_type='vip',
            quantity=2,
            total_amount=200.00,
            pidx='test_pid_123'
        )
        self.assertEqual(payment_order.status, 'initiated')
        self.assertEqual(payment_order.total_amount, 200.00)