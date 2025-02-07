
from rest_framework.permissions import BasePermission, SAFE_METHODS

class readonly (BasePermission):
    """custom permission to only allow organizer to edit an event."""

    def has_permission (self, request,view):
        if request.method in SAFE_METHODS:
            return True
    