from django.urls import path
from . import views
from django.shortcuts import render

urlpatterns = [
    path('', views.trip_list, name='trip_list'),
    path('order/<int:trip_id>/', views.create_order, name='create_order'),
    path('add_trip/', views.add_trip, name='add_trip'),
    path('register/', views.register, name='register'),
    path('profile/', views.user_profile, name='user_profile'),
    path('download_ticket/<int:order_id>/', views.download_ticket, name='download_ticket'),
    path('test/', lambda r: render(r, 'tickets/test.html'), name='test'),
]