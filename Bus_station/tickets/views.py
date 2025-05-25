from django.shortcuts import render, redirect
from .models import Trip, Order
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ['origin', 'destination', 'departure_time', 'price', 'seats_available', 'company']
        widgets = {
            'departure_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'company': forms.Select(attrs={'required': 'required'}),
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
                user=request.user,
                tickets_count=tickets_count
            )
            trip.seats_available -= tickets_count
            trip.save()
            return redirect('trip_list')
    return render(request, 'tickets/create_order.html', {'trip': trip})

@staff_member_required
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
            login(request, user)
            return redirect('trip_list')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def user_profile(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'tickets/user_profile.html', {'orders': orders})

@login_required
def download_ticket(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    
    # Создание PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ticket_{order.ticket_number}.pdf"'

    # Инициализация canvas
    p = canvas.Canvas(response, pagesize=A4)
    
    # Регистрация шрифта с поддержкой кириллицы
    font_path = os.path.join(os.path.dirname(__file__), 'static', 'fonts', 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
    p.setFont('DejaVuSans', 12)

    # Заголовок
    p.setFont('DejaVuSans', 16)
    p.drawString(50 * mm, 270 * mm, "Билет на автобус")
    
    # Информация о билете
    p.setFont('DejaVuSans', 12)
    p.drawString(50 * mm, 250 * mm, f"Номер билета: {order.ticket_number}")
    p.drawString(50 * mm, 240 * mm, f"Пассажир: {order.user.username}")
    p.drawString(50 * mm, 230 * mm, f"Рейс: {order.trip.origin} - {order.trip.destination}")
    p.drawString(50 * mm, 220 * mm, f"Компания: {order.trip.company.name if order.trip.company else 'Не указана'}")
    p.drawString(50 * mm, 210 * mm, f"Дата и время отправления: {order.trip.departure_time}")
    p.drawString(50 * mm, 200 * mm, f"Количество билетов: {order.tickets_count}")
    p.drawString(50 * mm, 190 * mm, f"Дата заказа: {order.created_at}")
    p.drawString(50 * mm, 180 * mm, f"Общая стоимость: {order.tickets_count * order.trip.price} руб.")

    # Завершение PDF
    p.showPage()
    p.save()
    return response