# """test for category api"""
# from django.contrib.auth import get_user_model
# from django.urls import reverse
# from django.test import TestCase

# from rest_framework import status
# from rest_framework.test import APIClient

# from core.models import Category , Events
# from Events.serializers import CategorySerializer

# CATEGORY_URL = reverse('Events:category-list')




# def create_events(user, **params):
#     """Create and return a sample event."""
#     defaults = {
#         'title': 'Sample Event Title',
#         'description': 'Sample description',
#         'link': 'http://example.com/events.pdf',
#         'created_at': '2025-01-02',
#         'event_dates':'2025-03-02',
#         'time':'00:00:00',
        
#     }
#     defaults.update(params)
#     event = Events.objects.create(user=user, **defaults)
#     return event
# def detail_url(category_id):
#     """Create and return a category detail url."""
#     return reverse('Events:category-detail', args=[category_id])


# def create_user(email="testuser@example.com",password='testpass123'):
#     """create  and return a user"""
#     return get_user_model().objects.create_user(email=email, password=password)

# class PublicCategoryApiTests(TestCase):
#     """Test unauthenticated API requests."""

#     def setUp(self):
#         self.client = APIClient()

#     def test_auth_required(self):
#         """Test auth is required for retrieving category."""
#         res = self.client.get(CATEGORY_URL)

#         self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

# #private authenticated api request

# class PrivateCategoryAPITests(TestCase):
#     """test authenticated api request"""
#     def setUp(self):
#         self.user = create_user()
#         self.client = APIClient()
#         self.client.force_authenticate(self.user)

#     def test_retrieve_category(self):
#         """Test retrieving a list of category."""
#         Category.objects.create(user=self.user, name='auction')
#         Category.objects.create(user=self.user, name='concert')

#         res = self.client.get(CATEGORY_URL)

#         categories = Category.objects.all().order_by('-name')
#         serializer = CategorySerializer(categories, many=True)
#         self.assertEqual(res.status_code, status.HTTP_200_OK)
#         self.assertEqual(res.data, serializer.data)

#     def test_category_limited_to_user(self):
#         """Test list of categories is limited to authenticated user."""
#         user2 = create_user(email='user2@example.com')
#         Category.objects.create(user=user2, name='concert')
#         category = Category.objects.create(user=self.user, name='localevents')

#         res = self.client.get(CATEGORY_URL)

#         self.assertEqual(res.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(res.data), 1)
#         self.assertEqual(res.data[0]['name'], category.name)
#         self.assertEqual(res.data[0]['id'], category.id)

#     def test_update_category(self):
#         """test updating a category"""
#         category = Category.objects.create(user=self.user, name='movienight')

#         payload = {'name': 'functions'}
#         url = detail_url(category.id)
#         res = self.client.patch(url, payload)

#         self.assertEqual(res.status_code, status.HTTP_200_OK)
#         category.refresh_from_db()
#         self.assertEqual(category.name, payload['name'])

#     def test_delete_category(self):
#         """Test deleting a category"""
#         category = Category.objects.create(user=self.user, name='concert')

#         url = detail_url(category.id)
#         res = self.client.delete(url)

#         self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
#         categories = Category.objects.filter(user=self.user)
#         self.assertFalse(categories.exists())


#     def test_filter_category_assigned_to_events(self):
#         """Test listing category to those assigned to events."""
#         c1 = Category.objects.create(user=self.user, name='concert')
#         c2 = Category.objects.create(user=self.user, name='local events')
#         user1= create_user(email='user2@example.com')
#         event=create_events(user=user1)
#         event.category.add(c1)

#         res = self.client.get(CATEGORY_URL, {'assigned_only': 1})

#         s1 = CategorySerializer(c1)
#         s2 = CategorySerializer(c2)
#         self.assertIn(s1.data, res.data)
#         self.assertNotIn(s2.data, res.data)

#     def test_filtered_category_unique(self):
#         """Test filtered category returns a unique list."""
#         category = Category.objects.create(user=self.user, name='auction')
#         Category.objects.create(user=self.user, name='concert')
#         user2 = create_user(email='user2@example.com')
#         event1=create_events(user=user2)
#         event2=create_events(user=user2)
#         event1.category.add(category)
#         event2.category.add(category)

#         res = self.client.get(CATEGORY_URL, {'assigned_only': 1})

#         self.assertEqual(len(res.data), 1)