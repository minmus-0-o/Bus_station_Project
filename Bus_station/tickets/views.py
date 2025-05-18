from django.shortcuts import render, redirect
from .models import Trip, Order
from django.utils import timezone

def trip_list(request):
    trips = Trip.objects.filter(departure_time__gte=timezone.now(), seats_available__gt=0)
    return render(request, 'tickets/trip_list.html', {'trips': trips})

def create_order(request, trip_id):
    trip = Trip.objects.get(id=trip_id)
    if request.method == 'POST':
        customer_name = request.POST['customer_name']
        customer_email = request.POST['customer_email']
        tickets_count = int(request.POST['tickets_count'])
        if tickets_count <= trip.seats_available:
            Order.objects.create(
                trip=trip,
                customer_name=customer_name,
                customer_email=customer_email,
                tickets_count=tickets_count
            )
            trip.seats_available -= tickets_count
            trip.save()
            return redirect('trip_list')
    return render(request, 'tickets/create_order.html', {'trip': trip})