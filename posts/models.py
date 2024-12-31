from django.conf import settings
from django.db import models

class Post(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    interested_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,  # Use this instead of 'auth.User'
        related_name='interested_posts',
        blank=True
    )

    def __str__(self):
        return self.title
