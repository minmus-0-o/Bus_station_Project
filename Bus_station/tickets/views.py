from django.shortcuts import render, redirect
from .models import Trip, Order
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ['origin', 'destination', 'departure_time', 'price', 'seats_available']
        widgets = {
            'departure_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

def trip_list(request):
    trips = Trip.objects.filter(departure_time__gte=timezone.now(), seats_available__gt=0)
    return render(request, 'tickets/trip_list.html', {'trips': trips})

@login_required
def create_order(request, trip_id):
    trip = Trip.objects.get(id=trip_id)
    if request.method == 'POST':
        tickets_count = int(request.POST['tickets_count'])
        if tickets_count <= trip.seats_available:
            Order.objects.create(
                trip=trip,
                user=request.user,  # Привязываем заказ к текущему пользователю
                tickets_count=tickets_count
            )
            trip.seats_available -= tickets_count
            trip.save()
            return redirect('trip_list')
    return render(request, 'tickets/create_order.html', {'trip': trip})

@login_required
def add_trip(request):
    if request.method == 'POST':
        form = TripForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('trip_list')
    else:
        form = TripForm()
    return render(request, 'tickets/add_trip.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Автоматический вход после регистрации
            return redirect('trip_list')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def user_profile(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'tickets/user_profile.html', {'orders': orders})