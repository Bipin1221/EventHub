from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext as _
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from core.models import PasswordResetToken,EmailVerificationToken

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password', 'name', 'role','bio','image']
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 8},
            # 'email': {'read_only': True},
            # 'role': {'read_only': True},
            'bio': {'required': False},
            'image': {'required': False},
          
        }

    def create(self, validated_data):
       
        user = User.objects.create_user(**validated_data)
        user.is_active = False  # Temporarily deactivate
        user.save()

        # Generate token
        token = EmailVerificationToken.objects.create(user=user)

        # Send email
        from django.core.mail import send_mail
        verification_link = f"http://localhost:5173/verify-email?token={token.token}"
        send_mail(
            subject="Verify your email",
            message=f"Click the link to verify your account: {verification_link}",
            from_email="noreply@eventhub.com",
            recipient_list=[user.email],
        )
        return user


    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get('request'),
            username=attrs['email'],
            password=attrs['password']
        )
        if not user:
            raise serializers.ValidationError(_('Unable to authenticate'))
        attrs['user'] = user
        return attrs

class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        validators=[validate_password]
    )
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect")
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New passwords must match")
        return data

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user with this email exists")
        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.UUIDField(required=True)
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,  # Match UserSerializer's length
        validators=[validate_password],
        style={'input_type': 'password'}
    )

    def validate_token(self, value):
        try:
            self.token_obj = PasswordResetToken.objects.get(token=value)
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid token")
        
        if self.token_obj.is_expired():
            self.token_obj.delete()
            raise serializers.ValidationError("Expired token")
        return value

    def validate(self, data):
        data['user'] = self.token_obj.user
        return data

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        PasswordResetToken.objects.filter(user=user).delete()