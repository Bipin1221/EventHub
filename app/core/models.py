"""Database models"""

from django.db import models
import uuid
import os
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)
from django.conf import settings
from django.utils import timezone
import uuid
from django.db import models
from django.conf import settings
from Events.utils import generate_qr_code

import qrcode
from io import BytesIO
from django.core.files.base import ContentFile



def event_image_file_path(instance, filename):
    """Generate file path for new event image."""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('uploads', 'events', filename)


class UserManager(BaseUserManager):
    """Manager for users."""
    def create_user(self, email, password=None, **extra_fields):
        """Create, save, and return a new user."""
        if not email:
            raise ValueError('User must have an email address.')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password):
        """Create and return a new superuser."""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system."""
    ROLE_CHOICES = [
        ('organizer', 'Organizer'),
        ('attendee', 'Attendee'),
    ]

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='attendee')

    objects = UserManager()
    # read_only_fields = ['role']
    USERNAME_FIELD = 'email'


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)  # Keep unique constraint
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.name = self.name.strip().lower()  # Normalize before save
        super().save(*args, **kwargs)



class Events(models.Model):
    """Event object."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateField(default=timezone.now)
    event_dates = models.DateField(default=timezone.now)
    link = models.CharField(max_length=255, blank=True)
    venue_name = models.CharField(max_length=150,blank= True)
    venue_location = models.CharField(max_length=150,blank= True)
    venue_capacity = models.IntegerField(blank=True, null=True)
    time_start = models.TimeField(default=timezone.now)
    category = models.ManyToManyField(Category, blank=True)
    image = models.ImageField(null=True, blank=True, upload_to=event_image_file_path)
    
    def __str__(self):
        return self.title


class EventImage(models.Model):
    """Model to store multiple images for an event."""
    event = models.ForeignKey(Events, on_delete=models.CASCADE, related_name='event_images')
    image = models.ImageField(upload_to='event_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


class Interest(models.Model):
    """Model to track attendees' interest in events."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Events, on_delete=models.CASCADE, related_name='interests')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'event')  # Prevent duplicate interests


class Comment(models.Model):
    """Model to allow attendees to comment on events."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Events, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Rating(models.Model):
    """Model to allow attendees to rate events."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Events, on_delete=models.CASCADE, related_name='ratings')
    value = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # Ratings from 1 to 5
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'event')  # Prevent duplicate ratings




class Ticket(models.Model):
    TICKET_TYPES = [
        ('VIP', 'VIP'),
        ('COMMON', 'Common')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Events, on_delete=models.CASCADE, related_name='tickets',null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets')
    ticket_type = models.CharField(max_length=10, choices=TICKET_TYPES, default='COMMON')
    quantity = models.PositiveIntegerField(default=1)  # Add quantity field
    purchased_at = models.DateTimeField(default=timezone.now)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    validated_count = models.PositiveIntegerField(default=0)

    def is_fully_validated(self):
        return self.validated_count >= self.quantity
    # Remove the unique_together constraint
    # class Meta:
    #     unique_together = ('event', 'user')

    def __str__(self):
        return f"{self.quantity}x {self.ticket_type} tickets for {self.user} - {self.event.title}"
    
    def save(self, *args, **kwargs):
        """Generate QR code without file system dependency"""
        if not self.qr_code:
            qr_img = qrcode.make(f"TICKET:{self.id}")
            buffer = BytesIO()
            qr_img.save(buffer, format='PNG')
            buffer.seek(0)
            
            self.qr_code.save(
                f"qr_{self.id}.png",
                ContentFile(buffer.getvalue()),
                save=False
            )
        super().save(*args, **kwargs)