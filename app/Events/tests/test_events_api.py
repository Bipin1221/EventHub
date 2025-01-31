from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import (Events,
                         Category)
import tempfile
import os 
from PIL import Image



from Events.serializers import EventsSerializer, EventsDetailSerializer


EVENTS_URL = reverse('Events:events-list')

def detail_url(event_id):
    """Create and return an event detail URL."""
    return reverse('Events:events-detail', args=[event_id])

def image_upload_url(events_id):
    """Create and return an image upload URL."""
    return reverse('Events:events-upload-image', args=[events_id])


def create_events(user, **params):
    """Create and return a sample event."""
    defaults = {
        'title': 'Sample Event Title',
        'description': 'Sample description',
        'link': 'http://example.com/events.pdf',
        'created_at': '2025-01-02',
        'event_dates':'2025-03-02',
        'time':'00:00:00',
        
    }
    defaults.update(params)
    event = Events.objects.create(user=user, **defaults)
    return event

def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)

class PublicEventsAPITests(TestCase):
    """Test unauthenticated API requests."""
    
    def setUp(self):
        """Set up the test client."""
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required to access the events list."""
        res = self.client.get(EVENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateEventAPITests(TestCase):
    """Test authenticated API requests."""
    
    def setUp(self):
        """Set up the test client and authenticated user."""
        self.client = APIClient()
        self.user = create_user(email='user@example.com', password='test123')
        self.client.force_authenticate(self.user)

    def test_retrieve_events(self):
        """Test retrieving a list of events."""
        create_events(user=self.user)
        create_events(user=self.user)

        res = self.client.get(EVENTS_URL)

        events = Events.objects.all().order_by('-id')
        serializer = EventsSerializer(events, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_events_list_limited_to_user(self):
        """Test that the list of events is limited to the authenticated user."""
        other_user = create_user(email='other@example.com', password='testpass123')
        create_events(user=other_user)
        create_events(user=self.user)

        res = self.client.get(EVENTS_URL)

        events = Events.objects.filter(user=self.user)
        serializer = EventsSerializer(events, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_events_detail(self):
        """Test retrieving event details."""
        event = create_events(user=self.user)
        url = detail_url(event.id)
        res = self.client.get(url)
        serializer = EventsDetailSerializer(event)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    # def test_create_event(self):
    #     """Test creating an event."""
    #     payload = {
    #     'title': 'Sample Event Title',
    #     'description': 'Sample description',
    #     'link': 'http://example.com/events.pdf',
    #     'created_at': '2025-01-02',
    #     'event_dates': '2025-03-02',
    #     'time': '00:00:00', 
        
            
    #     }

    #     res = self.client.post(EVENTS_URL, payload, format='json')

    #     # # Debugging: print response data if the test fails
    #     if res.status_code != status.HTTP_201_CREATED:
    #         print(res.data)  # This will show you the error message, if any

    #     self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    #     event = Events.objects.get(id=res.data['id'])

    #     # Validate that each field is correctly stored
    #     for k, v in payload.items():
    #         if k == "event_dates":
    #             self.assertEqual(str(getattr(event, k)), v)  # Date comparison
    #         elif k == "time":
    #             self.assertEqual(str(getattr(event, k)), v)  # Time comparison
    #         elif k=='category':
    #             continue
    #         else:
    #             self.assertEqual(str(getattr(event, k)), v)  # For other fields

    #     self.assertEqual(event.user, self.user)

    def test_partial_update(self):
        """Test partial update of a event."""
        original_link = 'https://example.com/event.pdf'
        event = create_events(
            user=self.user,
            title='Sample event title',
            link=original_link,
        )

        payload = {'title': 'New event title'}
        url = detail_url(event.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        event.refresh_from_db()
        self.assertEqual(event.title, payload['title'])
        self.assertEqual(event.link, original_link)
        self.assertEqual(event.user, self.user)

    # def test_full_update(self):
    #     """Test full update of event."""
    #     event = create_events(
    #         user=self.user,
    #         title='Sample event title',
    #         link='https://exmaple.com/event.pdf',
    #         description='Sample event description.',
            
    #     )

    #     payload = {
    #         'title': 'New event title',
    #         'link': 'https://example.com/new-event.pdf',
    #         'description': 'New event description',
    #         'created_at': '2025-01-02',
    #         'event_dates': '2025-03-02',
    #         'time': '00:00:00',  # Correct format without extraneous characters
            

    #         }

    #     url = detail_url(event.id)
    #     res = self.client.put(url, payload)

    #     # Debugging: print response data if the test fails
    #     if res.status_code != status.HTTP_200_OK:
    #         print(res.data)  # This will show you the error message, if any

    #     self.assertEqual(res.status_code, status.HTTP_200_OK)
    #     event.refresh_from_db()
    #     for k, v in payload.items():
    #         if k == "event_dates":
    #             self.assertEqual(str(getattr(event, k)), v)
    #         elif k == "time":
    #             self.assertEqual(str(getattr(event, k)), v)
    #         elif k=='category':
    #             continue
    #         else:
    #             self.assertEqual(str(getattr(event, k)), v)

    #     self.assertEqual(event.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the event user results in an error."""
        new_user = create_user(email='user2@example.com', password='test123')
        event = create_events(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(event.id)
        self.client.patch(url, payload)

        event.refresh_from_db()
        self.assertEqual(event.user, self.user)

    def test_delete_event(self):
        """Test deleting an event is successful."""
        event = create_events(user=self.user)

        url = detail_url(event.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Events.objects.filter(id=event.id).exists())

    def test_delete_other_users_event_error(self):
        """Test trying to delete another user's event results in error."""
        new_user = create_user(email='user2@example.com', password='test123')
        event = create_events(user=new_user)

        url = detail_url(event.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Events.objects.filter(id=event.id).exists())

    

    def test_create_event_with_new_category(self):
        """test creating a event with new category"""
        payload = {
            'title': 'New event title',
            'created_at': '2025-01-02',  # DateField format fixed
            'event_dates': '2025-03-02',  # ISO 8601 format with Z
            'time': '00:00:00',
            'category': [{'name': 'concert'}, {'name': 'localevent'}], 
        }
        res = self.client.post(EVENTS_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        events = Events.objects.filter(user=self.user)
        self.assertEqual(events.count(), 1)
        events = events[0]
        self.assertEqual(events.category.count(), 2)
        for category in payload['category']:
            exists = events.category.filter(
                name=category['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)



    def test_create_events_with_existing_category(self):
        """test creating a event with existing category"""
        category_auction = Category.objects.create(user=self.user, name='auction')
        payload = {
            'title': 'test title',
            'created_at': '2025-01-02',
            'event_dates': '2025-03-02',
            'time': '00:00:00',
            'category': [{'name': 'auction'}, {'name': 'localevent'}], 
        }
        res = self.client.post(EVENTS_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        events = Events.objects.filter(user=self.user)
        self.assertEqual(events.count(), 1)
        event = events[0]
        self.assertEqual(event.category.count(), 2)
        self.assertIn(category_auction, event.category.all())
        for category in payload['category']:
            exists = event.category.filter(
                name=category['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    
    def test_create_category_on_update(self):
        """Test create category when updating a event."""
        event = create_events(user=self.user)

        payload = {'category': [{'name': 'concert'}]}
        url = detail_url(event.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_category = Category.objects.get(user=self.user, name='concert')
        self.assertIn(new_category, event.category.all())

    def test_update_events_assign_category(self):
        """Test assigning an existing category when updating a events."""
        category_movietime = Category.objects.create(user=self.user, name='movietime')
        event = create_events(user=self.user)
        event.category.add(category_movietime)

        category_concert = Category.objects.create(user=self.user, name='concert')
        payload = {'category': [{'name': 'concert'}]}
        url = detail_url(event.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(category_concert, event.category.all())
        self.assertNotIn(category_movietime, event.category.all())

    def test_clear_event_category(self):
        """Test clearing a event category."""
        category = Category.objects.create(user=self.user, name='concert')
        event = create_events(user=self.user)
        event.category.add(category)

        payload = {'category': []}
        url = detail_url(event.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(event.category.count(), 0)

    def test_filter_by_category(self):
        """Test filtering events by category."""
        r1 = create_events(user=self.user, title='street festival')
        r2 = create_events(user=self.user, title='concert')
        c1 = Category.objects.create(user=self.user, name='games')
        c2 = Category.objects.create(user=self.user, name='elements')
        r1.category.add(c1)
        r2.category.add(c2)
        r3 = create_events(user=self.user, title='auction')

        params = {'category': f'{c1.id},{c2.id}'}
        res = self.client.get(EVENTS_URL, params)

        s1 = EventsSerializer(r1)
        s2 = EventsSerializer(r2)
        s3 = EventsSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageUploadTests(TestCase):
    """Tests for the image upload API."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'password123',
        )
        self.client.force_authenticate(self.user)
        self.events = create_events(user=self.user)

    def tearDown(self):
        self.events.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a events."""
        url = image_upload_url(self.events.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.events.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.events.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image."""
        url = image_upload_url(self.events.id)
        payload = {'image': 'notanimage'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
