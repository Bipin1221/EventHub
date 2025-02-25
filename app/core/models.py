"""Dataase models"""

from django.db import models
import uuid
import os
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)
from django.conf import settings


def event_image_file_path(instance,filename):
    """generate file path for new event image."""
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'

    return os.path.join('uploads', 'events', filename)



class UserManager(BaseUserManager):
     """manager for users"""
     def create_user(self,email,password = None,**extra_field):
        """create save and return a new user"""
       
        if not email:
            raise ValueError('user must have an email adress.')
        user = self.model(email=self.normalize_email(email), **extra_field)
        user.set_password(password)
        user.save(using=self._db)
        return user
     
     def create_superuser(self,email,password):
         """create and return a new superuser"""
         user = self.create_user(email,password)
         user.is_staff =True
         user.is_superuser = True
         user.save(using=self._db)

         return user

class User(AbstractBaseUser,PermissionsMixin):
    """user in the system"""

    email = models.EmailField(max_length=255,unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default = True)
    is_staff = models.BooleanField(default = False)
    
    objects=UserManager()

    USERNAME_FIELD = 'email'

from django.utils import timezone

class Events(models.Model):
    """Event object."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete= models.CASCADE,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateField(default=timezone.now)  # Use timezone-aware datetime
    event_dates = models.DateField(default=timezone.now)  # Use timezone-aware datetime
    link = models.CharField(max_length=255, blank=True)
    time = models.TimeField(default=timezone.now)
    category=models.ManyToManyField('Category',blank=True)
    image=models.ImageField(null=True,blank=True, upload_to=event_image_file_path)

    def __str__(self):
        return self.title

class Category(models.Model):
    """category for filtering events"""
    name=models.CharField(max_length=255)
    user=models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    def __str__(self):
        return self.name
    





