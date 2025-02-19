"""
URL mappings for the user API.
"""
from django.urls import path

from user import views


app_name = 'user'

urlpatterns = [
    
    path('sign-up/', views.CreateUserView.as_view(), name='sign-up'),
    path('login/', views.CreateTokenView.as_view(), name='login'),
    path('verify-token/', views.VerifyTokenView.as_view(), name='verify-token'),
    path('profile/', views.ManageUserView.as_view(), name='profile'),
]
