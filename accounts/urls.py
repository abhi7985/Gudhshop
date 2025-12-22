from django.urls import path
from . import views
from . import api_views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.phone_login, name='phone_login'),
    path('verify/', views.verify_otp, name='verify_otp'),
    path('logout/', views.logout_view, name='logout'),
    path("send-otp/", api_views.send_otp, name="api_send_otp"),
    path("verify-otp/", api_views.verify_otp, name="api_verify_otp"),
]