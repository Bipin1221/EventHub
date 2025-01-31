"""tests for models """
from django.test import TestCase
from core import models
from unittest.mock import patch
from django.contrib.auth import get_user_model

def create_user(email='test@gexample.copm',password='testpass123'):
    """"crate and return a new user"""
    return get_user_model().objects.create_user(email,password)
    

class Modeltests(TestCase):
    """test models."""



    def test_create_user_with_email_successful(self):
        """Test creating user successful."""
        email='test@example.com'
        password='testpass123'
        user = get_user_model().objects.create_user(
            email = email,
            password = password,
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
    
    def test_new_use_email_normalized(self):
        """Test email is normalized for ew users"""
        sample_email = [


            ['test1@Example.com','test1@example.com'],
            ['Test2@Example.com','Test2@example.com'],
            ['TEST3@Example.com','TEST3@example.com'],
            ['test4@Example.COM','test4@example.com'],
        ]
        for email, expected in sample_email:
            user=get_user_model().objects.create_user(email,'sample123')
            self.assertEqual(user.email,expected)
    def test_new_user_without_emai_raise_error(self):
        """Test that creating withotu email error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('','test12345')

    def test_create_superuser(self):
        """test creating super user"""
        user= get_user_model().objects.create_superuser(
            'test@example.com','test12345'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
    
    def create_event(self):
        """test creating a event is successful """
        user=get_user_model().objects.create_user(
            'test@example.com',
            'testpass123',
        )
        event = models.Event.object.create(
            user=user,
            title="sample event",
            created_at ='2025-02-12',
            event_dates ='2025-04-03',
            time = "00:00:00", 
            description = 'sample event description',
            )
        self.assertEqual(str(event),event.title)

    
    def test_create_category(self):
        """test creating a category successful"""
        user=create_user()
        category= models.Category.objects.create(user=user,name='category1')
        self.assertEqual(str(category),category.name)
        

    @patch('core.models.uuid.uuid4')
    def test_event_file_name_uuid(self, mock_uuid):
        """Test generating image path."""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.event_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/events/{uuid}.jpg')