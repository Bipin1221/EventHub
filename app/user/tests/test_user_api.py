from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from django.core import mail
from rest_framework.authtoken.models import Token
USER_URL = '/api/user/me/'
CREATE_USER_URL = '/api/user/create/'
TOKEN_URL = '/api/user/token/'
VERIFY_TOKEN_URL = '/api/user/verify-token/'

def create_user(**params):
    return get_user_model().objects.create_user(**params)

class PublicUserApiTests(TestCase):
    """Test the users API (public)"""
    
    def setUp(self):
        self.client = APIClient()
        
    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful"""
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test Name',
            'role': 'attendee'
        }
        res = self.client.post(CREATE_USER_URL, payload)
        
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)
        self.assertEqual(user.role, 'attendee')
        
    def test_user_with_email_exists_error(self):
        """Test creating user that already exists fails"""
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test Name',
            'role': 'organizer'
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)
        
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_password_too_short_error(self):
        """Test that password must be more than 8 characters"""
        payload = {
            'email': 'test@example.com',
            'password': 'pw',
            'name': 'Test Name',
            'role': 'attendee'
        }
        res = self.client.post(CREATE_USER_URL, payload)
        
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)
        
    @patch('user.views.send_mail')
    def test_create_token_for_user(self, mock_send_mail):
        """Test that a token is created and email sent for valid credentials"""
        user_details = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test Name',
            'role': 'attendee'
        }
        create_user(**user_details)
        
        payload = {
            'email': user_details['email'],
            'password': user_details['password']
        }
        res = self.client.post(TOKEN_URL, payload)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('message', res.data)
        mock_send_mail.assert_called_once()
        
        # Verify old tokens are deleted and new one created
        user = get_user_model().objects.get(email=user_details['email'])
        tokens = Token.objects.filter(user=user)
        self.assertEqual(tokens.count(), 1)
        
    def test_create_token_invalid_credentials(self):
        """Test that token is not created for invalid credentials"""
        create_user(email='test@example.com', password='correctpass')
        payload = {'email': 'test@example.com', 'password': 'wrongpass'}
        res = self.client.post(TOKEN_URL, payload)
        
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)
        
    def test_create_token_no_user(self):
        """Test that token is not created if user doesn't exist"""
        payload = {'email': 'nonexistent@example.com', 'password': 'testpass'}
        res = self.client.post(TOKEN_URL, payload)
        
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_verify_valid_token(self):
        """Test verifying a valid authentication token"""
        user = create_user(email='test@example.com', password='testpass')
        token = Token.objects.create(user=user)
        
        payload = {'token': token.key}
        res = self.client.post(VERIFY_TOKEN_URL, payload)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['user_id'], user.id)
        
    def test_verify_invalid_token(self):
        """Test verifying an invalid token returns error"""
        payload = {'token': 'invalidtoken'}
        res = self.client.post(VERIFY_TOKEN_URL, payload)
        
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('token', res.data)
        
class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication"""
    
    def setUp(self):
        self.user = create_user(
            email='test@example.com',
            password='testpass123',
            name='Test Name',
            role='organizer'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user"""
        res = self.client.get(USER_URL)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'email': self.user.email,
            'name': self.user.name,
            'role': self.user.role
        })
        
    def test_post_me_not_allowed(self):
        """Test that POST is not allowed on the me URL"""
        res = self.client.post(USER_URL, {})
        
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
    def test_update_user_profile(self):
        """Test updating the user profile for authenticated user"""
        payload = {
             'name': 'New Name', 
            'password': 'newpassword123',
            'current_password': 'testpass123'  # Add if your API requires this
        }
    
        res = self.client.patch(USER_URL, payload)
    
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
    def test_update_user_role_not_allowed(self):
        """Test that users can't modify their role through API"""
        payload = {'role': 'attendee'}
        res = self.client.patch(USER_URL, payload)
    
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, 'organizer')
        # Check that role didn't change in response
        self.assertEqual(res.data['role'], 'organizer')
        self.assertEqual(res.status_code, status.HTTP_200_OK)