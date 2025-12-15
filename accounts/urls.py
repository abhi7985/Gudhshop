from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.phone_login, name='phone_login'),
    path('verify/', views.verify_otp, name='verify_otp'),
    path('logout/', views.logout_view, name='logout'),
]