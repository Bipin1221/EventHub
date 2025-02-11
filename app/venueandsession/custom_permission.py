from rest_framework import permissions

class IsEventOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return True

    def has_object_permission(self, request, view, obj):
        # Only allow owners to modify their own event's sessions
        return obj.event.owner == request.user
