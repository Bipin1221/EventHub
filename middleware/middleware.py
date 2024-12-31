from django.http import HttpResponseForbidden

class OrganizerOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/posts/") and request.user.is_authenticated:
            restricted_paths = ["/create/", "/update/", "/delete/"]
            if any(request.path.endswith(path) for path in restricted_paths) and not request.user.is_staff:
                return HttpResponseForbidden("You are not allowed to perform this action.")
        return self.get_response(request)

