# user/tests/_api.py
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from core.models import User
from django.utils.translation import gettext as _
from user.serializers import (
    UserSerializer,
    AuthTokenSerializer,
)
User = get_user_model()

class UserModelTests(TestCase):
    """Test the user model and manager."""
    
    def test_create_user_with_email_successful(self):
        """Test creating a user with an email is successful"""
        email = 'test@example.com'
        password = 'testpass123'
        user = User.objects.create_user(
            email=email,
            password=password,
            name='Test User',
            role='attendee'
        )
        
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertEqual(user.role, 'attendee')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
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
    
    def test_new_user_without_email_raises_error(self):
        """Test creating user without email raises error"""
        with self.assertRaises(ValueError):
            User.objects.create_user('', 'test123')
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        user = User.objects.create_superuser(
            'admin@example.com',
            'test123'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertEqual(user.role, 'attendee')  # Default role
    
    def test_user_str(self):
        """Test the user string representation"""
        user = User.objects.create_user(
            'test@example.com',
            'testpass123',
            name='Test User'
        )
        self.assertEqual(str(user), user.email)

class UserSerializerTests(TestCase):
    """Test the user serializer."""
    
    def test_create_user_serializer(self):
        """Test creating user with serializer"""
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User',
            'role': 'attendee'
        }
        serializer = UserSerializer(data=payload)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        
        self.assertEqual(user.email, payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertEqual(user.role, payload['role'])
    
    def test_update_user_serializer(self):
        """Test updating user with serializer"""
        user = User.objects.create_user(
            'test@example.com',
            'testpass123',
            name='Old Name'
        )
        payload = {'name': 'New Name', 'password': 'newpass123'}
        serializer = UserSerializer(user, data=payload, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        
        self.assertEqual(updated_user.name, 'New Name')
        self.assertTrue(updated_user.check_password('newpass123'))

class AuthTokenSerializerTests(TestCase):
    """Test the authentication token serializer."""
    
    def test_create_token_valid_credentials(self):
        """Test token creation with valid credentials"""
        user = User.objects.create_user(
            'test@example.com',
            'testpass123'
        )
        serializer = AuthTokenSerializer(data={
            'email': 'test@example.com',
            'password': 'testpass123'
        }, context={'request': None})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['user'], user)
    
    def test_create_token_invalid_credentials(self):
        """Test token creation with invalid credentials"""
        User.objects.create_user('test@example.com', 'testpass123')
        serializer = AuthTokenSerializer(data={
            'email': 'test@example.com',
            'password': 'wrongpass'
        }, context={'request': None})
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

class UserViewsTests(APITestCase):
    """Test the user API views."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User',
            role='attendee'
        )
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.signup_url = reverse('user:sign-up')
        self.login_url = reverse('user:login')
        self.profile_url = reverse('user:profile')
        self.change_password_url = reverse('user:change-password')
    
    # Authentication Tests
    def test_create_token_success(self):
        """Test user login with valid credentials"""
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['email'], self.user.email)
    
    def test_create_token_invalid_credentials(self):
        """Test user login with invalid credentials"""
        payload = {'email': 'test@example.com', 'password': 'wrongpass'}
        response = self.client.post(self.login_url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)
    
    # User Registration Tests
    def test_user_registration_success(self):
        """Test successful user registration"""
        payload = {
            'email': 'new@example.com',
            'password': 'newpass123',
            'name': 'New User',
            'role': 'attendee'
        }
        response = self.client.post(self.signup_url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', response.data['data'])
    
    def test_user_registration_duplicate_email(self):
        """Test registration with existing email fails"""
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User'
        }
        response = self.client.post(self.signup_url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    # Profile Management Tests
    def test_retrieve_profile_unauthorized(self):
        """Test authentication is required for profile"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_retrieve_profile_authorized(self):
        """Test retrieving profile for logged in user"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)
    
    def test_update_profile(self):
        """Test updating user profile"""
        self.client.force_authenticate(user=self.user)
        payload = {'name': 'Updated Name'}
        response = self.client.patch(self.profile_url, payload)
        
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.name, 'Updated Name')
    
    def test_prevent_role_update_by_non_admin(self):
        """Test non-admins can't update their role"""
        self.client.force_authenticate(user=self.user)
        payload = {'role': 'organizer'}
        response = self.client.patch(self.profile_url, payload)
        
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.role, 'attendee')
    
    # Password Change Tests
    def test_password_change_success(self):
        """Test successful password change"""
        self.client.force_authenticate(user=self.user)
        payload = {
            'current_password': 'testpass123',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }
        response = self.client.post(self.change_password_url, payload)
        
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.check_password('newpass123'))
    
    def test_password_change_wrong_current(self):
        """Test password change with wrong current password"""
        self.client.force_authenticate(user=self.user)
        payload = {
            'current_password': 'wrongpass',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }
        response = self.client.post(self.change_password_url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('current_password', response.data)
    
    # Admin Management Tests
    # def test_admin_user_update(self):
    #     """Test admin can update any user"""
    #     self.client.force_authenticate(user=self.admin)
    #     url = reverse('user:admin-manage-user', kwargs={'pk': self.user.pk})
    #     payload = {'role': 'organizer'}
    #     response = self.client.patch(url, payload)
        
    #     self.user.refresh_from_db()
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(self.user.role, 'organizer')
    
    # def test_non_admin_cant_access_admin_endpoint(self):
    #     """Test regular users can't access admin endpoints"""
    #     self.client.force_authenticate(user=self.user)
    #     url = reverse('user:admin-manage-user', kwargs={'pk': self.user.pk})
    #     response = self.client.patch(url, {})
        
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class PasswordChangeValidationTests(APITestCase):
    """Test password change validation scenarios"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse('user:change-password')
    
    def test_password_mismatch(self):
        """Test new password confirmation mismatch"""
        payload = {
            'current_password': 'testpass123',
            'new_password': 'newpass123',
            'confirm_password': 'differentpass'
        }
        response = self.client.post(self.url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_weak_password(self):
        """Test validation of password strength"""
        payload = {
            'current_password': 'testpass123',
            'new_password': '123',
            'confirm_password': '123'
        }
        response = self.client.post(self.url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)