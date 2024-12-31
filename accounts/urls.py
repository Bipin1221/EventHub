from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('organizer_dashboard/', views.organizer_dashboard, name='organizer_dashboard'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),

    path('login/organizer/', views.organizer_login_view, name='organizer_login'),
    path('login/user/', views.user_login_view, name='user_login'),
    path('signup/organizer/', views.organizer_signup_view, name='organizer_signup'),
    path('signup/user/', views.user_signup_view, name='user_signup'),



]