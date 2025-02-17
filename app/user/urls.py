"""
URL mappings for the user API.
"""
from django.urls import path

from user import views


app_name = 'user'

urlpatterns = [
    path('sing-up/', views.CreateUserView.as_view(), name='sing-up'),
    path('login/', views.CreateTokenView.as_view(), name='login'),
    path('verify-login/', views.VerifyTokenView.as_view(), name='verify-login'),
    path('profile/', views.ManageUserView.as_view(), name='profile'),
]
