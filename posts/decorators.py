from functools import wraps
from django.http import HttpResponseForbidden

def organizer_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden("You are not allowed to perform this action.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

