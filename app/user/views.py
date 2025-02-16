"""
Views for the user API.
"""
from rest_framework import generics, authentication, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.settings import api_settings

from django.core.mail import send_mail
from django.conf import settings

from user.serializers import UserSerializer, AuthTokenSerializer, VerifyTokenSerializer
from django.contrib.auth import get_user_model


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system."""
    serializer_class = UserSerializer


class CreateTokenView(APIView):
    """Create a new auth token for user and send it via email."""
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        Token.objects.filter(user=user).delete()
        new_token = Token.objects.create(user=user)

        # Send the token to the user's email
        send_mail(
            subject="Your Authentication Token",
            message=f"Your authentication token is: {new_token.key}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return Response({"message": "Token sent to your email.",
                         "role": user.role,
                          "email": user.email,
                           "name": user.name }, status=200)


class VerifyTokenView(APIView):
    """Verify authentication token."""
    serializer_class = VerifyTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = VerifyTokenSerializer(data=request.data)

        if serializer.is_valid():
            token_key = serializer.validated_data["token"]
            token = Token.objects.get(key=token_key)

            return Response(
                {"message": "Token is valid.",
                  "user_id": token.user.id,
                  "role": token.user.role,
                "email": token.user.email,
                "name": token.user.name},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user."""
    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve and return the authenticated user."""
        return self.request.user

    def update(self, request, *args, **kwargs):
        """Custom update to prevent role change by non-admins."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Prevent role update if the user is not an admin
        if 'role' in serializer.validated_data and not request.user.is_staff:
            serializer.validated_data.pop('role')

        self.perform_update(serializer)
        return Response(serializer.data)


class ManageUserByAdminView(generics.RetrieveUpdateAPIView):
    """Manage user details by admin."""
    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    # Only Admin
    permission_classes = [permissions.IsAuthenticated,
                          permissions.IsAdminUser]

    queryset = get_user_model().objects.all()  # Need to fetch user
    lookup_field = 'pk'  # look up with pk

