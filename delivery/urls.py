from django.urls import path
from . import views

app_name = 'delivery'

urlpatterns = [
    path('login/', views.delivery_login, name='login'),
    path('logout/', views.delivery_logout, name='logout'),
    path('dashboard/', views.delivery_dashboard, name='dashboard'),
]
